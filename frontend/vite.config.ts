import { execFile } from 'node:child_process'
import fs from 'node:fs/promises'
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

const DEMO_IMAGES_DIR = '/home/aleosh/Imágenes/test'

const GTK_PICKER_SCRIPT = `
import os, pathlib, sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

target_dir = sys.argv[1]
dialog = Gtk.FileChooserDialog(
    title='Elegir imagen',
    action=Gtk.FileChooserAction.OPEN,
)
dialog.add_buttons(
    '_Cancelar', Gtk.ResponseType.CANCEL,
    '_Abrir', Gtk.ResponseType.OK,
)
dialog.set_keep_above(True)

img_filter = Gtk.FileFilter()
img_filter.set_name('Imágenes (JPEG, PNG, WEBP)')
for mime in ('image/jpeg', 'image/png', 'image/webp'):
    img_filter.add_mime_type(mime)
for pattern in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
    img_filter.add_pattern(pattern)
dialog.add_filter(img_filter)

if os.path.isdir(target_dir):
    dialog.set_current_folder_uri(pathlib.Path(target_dir).as_uri())

response = dialog.run()
selected = dialog.get_filename() if response == Gtk.ResponseType.OK else ''
dialog.destroy()
while Gtk.events_pending():
    Gtk.main_iteration()
if selected:
    print(selected)
`

function mimeFromExt(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase()
  if (ext === '.png') return 'image/png'
  if (ext === '.webp') return 'image/webp'
  return 'image/jpeg'
}

function demoImagePickerPlugin(): Plugin {
  return {
    name: 'demo-image-picker',
    configureServer(server) {
      server.middlewares.use('/__demo_pick_image', (_req, res) => {
        execFile('/usr/bin/python3', ['-c', GTK_PICKER_SCRIPT, DEMO_IMAGES_DIR], async (err, stdout) => {
          res.setHeader('Content-Type', 'application/json')
          if (err) {
            res.statusCode = 500
            res.end(JSON.stringify({ error: err.message }))
            return
          }
          const selectedPath = stdout.trim()
          if (!selectedPath) {
            res.statusCode = 200
            res.end(JSON.stringify({ cancelled: true }))
            return
          }
          try {
            const buffer = await fs.readFile(selectedPath)
            res.statusCode = 200
            res.end(
              JSON.stringify({
                cancelled: false,
                name: path.basename(selectedPath),
                type: mimeFromExt(selectedPath),
                data: buffer.toString('base64'),
              }),
            )
          } catch (readErr) {
            res.statusCode = 500
            res.end(JSON.stringify({ error: readErr instanceof Error ? readErr.message : 'Read error' }))
          }
        })
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), demoImagePickerPlugin()],
  server: {
    proxy: {
      '/graphql': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: false,
      },
    },
  },
})
