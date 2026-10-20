-- Mock catalog for local development. Prices are stored in MXN cents.
-- Run after Alembic has created the sales schema.

BEGIN;

INSERT INTO categories (id, name) VALUES
    ('cat-shampoo', 'Shampoo'),
    ('cat-boots', 'Botas'),
    ('cat-mice', 'Mouse'),
    ('cat-fans', 'Ventiladores'),
    ('cat-gifts', 'Regalos'),
    ('cat-accessories', 'Accesorios')
ON CONFLICT (id) DO NOTHING;

INSERT INTO providers (id, name, address, logo_url) VALUES
    ('prov-care', 'Natura Care México', 'Av. Insurgentes Sur 1602, Ciudad de México', 'https://placehold.co/256x256/0F766E/FFFFFF.png?text=Natura+Care'),
    ('prov-outdoor', 'Sierra Norte Outfitters', 'Av. Universidad 1001, Monterrey, Nuevo León', 'https://placehold.co/256x256/78350F/FFFFFF.png?text=Sierra+Norte'),
    ('prov-tech', 'Pixel Supply', 'Av. Vallarta 3300, Guadalajara, Jalisco', 'https://placehold.co/256x256/1E3A8A/FFFFFF.png?text=Pixel+Supply'),
    ('prov-home', 'Casa Brisa', 'Blvd. Atlixco 3156, Puebla, Puebla', 'https://placehold.co/256x256/0369A1/FFFFFF.png?text=Casa+Brisa'),
    ('prov-gifts', 'Órbita Regalos', 'Calle República de Cuba 43, Ciudad de México', 'https://placehold.co/256x256/6D28D9/FFFFFF.png?text=Orbita+Regalos'),
    ('prov-style', 'Tiempo y Vista', 'Av. Patria 1891, Zapopan, Jalisco', 'https://placehold.co/256x256/111827/FFFFFF.png?text=Tiempo+y+Vista')
ON CONFLICT (id) DO NOTHING;

INSERT INTO products (id, name, description, price_list_cents, provider_id, category_id) VALUES
    ('prod-shampoo-01', 'Shampoo Hidratación Coco 400 ml', 'Shampoo hidratante de uso diario con aroma a coco para cabello seco; fórmula mock sin sulfatos.', 18900, 'prov-care', 'cat-shampoo'),
    ('prod-shampoo-02', 'Shampoo Equilibrio Herbal 350 ml', 'Limpieza suave con extractos herbales para cabello normal a graso y acabado fresco.', 16500, 'prov-care', 'cat-shampoo'),
    ('prod-shampoo-03', 'Shampoo Reparación Keratina 500 ml', 'Fórmula reparadora con keratina para cabello teñido o maltratado por calor.', 22900, 'prov-care', 'cat-shampoo'),
    ('prod-shampoo-04', 'Shampoo Anticaspa Menta 400 ml', 'Shampoo refrescante con menta para limpieza profunda del cuero cabelludo.', 19900, 'prov-care', 'cat-shampoo'),

    ('prod-boots-01', 'Botas Senderismo Roble', 'Botas de senderismo color café con suela de alto agarre y soporte acolchado al tobillo.', 149900, 'prov-outdoor', 'cat-boots'),
    ('prod-boots-02', 'Botas Urbanas Chelsea Ébano', 'Botas Chelsea negras de piel sintética con paneles elásticos y suela antiderrapante.', 119900, 'prov-outdoor', 'cat-boots'),
    ('prod-boots-03', 'Botas Montaña Boreal', 'Botas térmicas de media caña con exterior resistente al agua para clima frío.', 179900, 'prov-outdoor', 'cat-boots'),
    ('prod-boots-04', 'Botas Trabajo Cobre', 'Botas de trabajo color miel con puntera reforzada y suela de caucho de uso rudo.', 159900, 'prov-outdoor', 'cat-boots'),

    ('prod-mouse-01', 'Mouse Inalámbrico Pulse M10', 'Mouse inalámbrico compacto de 1600 DPI, receptor USB y autonomía de hasta seis meses.', 34900, 'prov-tech', 'cat-mice'),
    ('prod-mouse-02', 'Mouse Ergonómico Arc M20', 'Mouse vertical ergonómico con seis botones y sensibilidad ajustable de hasta 2400 DPI.', 64900, 'prov-tech', 'cat-mice'),
    ('prod-mouse-03', 'Mouse Gaming Nova RGB', 'Mouse gaming con sensor óptico de 7200 DPI, siete botones programables e iluminación RGB.', 79900, 'prov-tech', 'cat-mice'),
    ('prod-mouse-04', 'Mouse Bluetooth Slate', 'Mouse Bluetooth silencioso de perfil bajo, compatible con Windows, macOS y tabletas.', 49900, 'prov-tech', 'cat-mice'),

    ('prod-fan-01', 'Ventilador de Mesa Brisa 12', 'Ventilador oscilatorio de mesa de 12 pulgadas con tres velocidades e inclinación ajustable.', 74900, 'prov-home', 'cat-fans'),
    ('prod-fan-02', 'Ventilador de Pedestal Aire 16', 'Ventilador de pedestal de 16 pulgadas, altura ajustable y rejilla de seguridad.', 109900, 'prov-home', 'cat-fans'),
    ('prod-fan-03', 'Ventilador Compacto Nube', 'Ventilador compacto para escritorio con dos velocidades y operación silenciosa.', 42900, 'prov-home', 'cat-fans'),
    ('prod-fan-04', 'Ventilador Torre Boreal', 'Ventilador tipo torre con oscilación, temporizador de dos horas y tres modos de aire.', 139900, 'prov-home', 'cat-fans'),

    ('prod-gift-01', 'Funko Pop Batman Classic', 'Figura coleccionable estilo Funko Pop de Batman clásico con traje negro y cinturón amarillo.', 39900, 'prov-gifts', 'cat-gifts'),
    ('prod-gift-02', 'Funko Pop Batman Blue & Grey', 'Figura coleccionable estilo Funko Pop de Batman con traje azul y gris en pose heroica.', 42900, 'prov-gifts', 'cat-gifts'),
    ('prod-gift-03', 'Pato de Hule Clásico', 'Pato de hule amarillo flotante con pico naranja, ideal para baño o decoración divertida.', 9900, 'prov-gifts', 'cat-gifts'),
    ('prod-gift-04', 'Pato de Hule Capitán', 'Pato de hule amarillo con diseño de capitán; juguete flotante de vinilo suave.', 12900, 'prov-gifts', 'cat-gifts'),
    ('prod-gift-05', 'Esfera Solar 3D 6 cm', 'Esfera de cristal con sistema solar grabado en 3D y base de madera con luz LED cálida.', 44900, 'prov-gifts', 'cat-gifts'),
    ('prod-gift-06', 'Esfera Galaxia 3D 8 cm', 'Esfera de cristal de 8 cm con planetas grabados, base iluminada y alimentación USB.', 59900, 'prov-gifts', 'cat-gifts'),

    ('prod-accessory-01', 'Lentes de Sol Noir', 'Lentes de sol negros con armazón clásico, mica polarizada y protección UV400.', 54900, 'prov-style', 'cat-accessories'),
    ('prod-accessory-02', 'Lentes de Sol Riviera', 'Lentes de sol con armazón carey, mica degradada y protección UV400.', 62900, 'prov-style', 'cat-accessories'),
    ('prod-accessory-03', 'Reloj Analógico Heritage', 'Reloj analógico con carátula blanca, caja de acero y correa de piel café.', 149900, 'prov-style', 'cat-accessories'),
    ('prod-accessory-04', 'Reloj Acero Meridian', 'Reloj analógico de acero inoxidable con carátula azul y resistencia al agua de 5 ATM.', 219900, 'prov-style', 'cat-accessories'),

    ('prod-shampoo-05', 'Shampoo Volumen Romero 300 ml', 'Shampoo ligero con aroma a romero para aportar cuerpo al cabello fino.', 17900, 'prov-care', 'cat-shampoo'),
    ('prod-boots-05', 'Botas Lluvia Grafito', 'Botas impermeables de media caña con acabado grafito y suela texturizada.', 89900, 'prov-outdoor', 'cat-boots'),
    ('prod-mouse-05', 'Mouse USB Core M5', 'Mouse óptico alámbrico de tres botones y 1200 DPI para oficina o estudio.', 19900, 'prov-tech', 'cat-mice'),
    ('prod-fan-05', 'Ventilador Circulador Polar', 'Circulador de aire compacto con cabezal inclinable y tres niveles de potencia.', 84900, 'prov-home', 'cat-fans')
ON CONFLICT (id) DO NOTHING;

INSERT INTO media_products (id, url, product_id, is_main) VALUES
    ('media-shampoo-01', 'https://fitnessbeautyart.com/wp-content/uploads/2024/02/1bfa5f59thumbnail-682x1024.jpeg', 'prod-shampoo-01', TRUE),
    ('media-shampoo-02', 'https://st.depositphotos.com/3058419/54874/i/450/depositphotos_548743700-stock-photo-plastic-shampoo-bottle-isolated-white.jpg', 'prod-shampoo-02', TRUE),
    ('media-shampoo-03', 'https://developers.openai.com/cookbook/assets/images/extract_product_gpt-image-2.png', 'prod-shampoo-03', TRUE),
    ('media-shampoo-04', 'https://tiimg.tistatic.com/fp/1/007/620/rescue-hair-from-damage-made-from-natural-ingredients-and-gentle-green-hair-shampoo-773.jpg', 'prod-shampoo-04', TRUE),
    ('media-shampoo-05', 'https://scx2.b-cdn.net/gfx/news/hires/2020/shampoobottle.jpg', 'prod-shampoo-05', TRUE),

    ('media-boots-01', 'https://contents.mediadecathlon.com/p2904892/k%247e0c1b8961d34b51491cb8227b85eecb/picture.jpg', 'prod-boots-01', TRUE),
    ('media-boots-02', 'https://jans.com/cdn/shop/files/SOR00233_Tobacco-and-Black.02.jpg?v=1764449380&width=1080', 'prod-boots-02', TRUE),
    ('media-boots-03', 'https://beredd.se/app/uploads/2022/09/Graninge-Fjall-Fodrad3-688x688.jpg.webp', 'prod-boots-03', TRUE),
    ('media-boots-04', 'https://shopping.c.yimg.jp/lib/nextfocus/2000108301_1c019.jpg', 'prod-boots-04', TRUE),
    ('media-boots-05', 'https://respect-shoes.ru/upload/iblock/4fe/9m58w5ou7293rgxaddzt9hbxxygc30of.JPG', 'prod-boots-05', TRUE),

    ('media-mouse-01', 'https://images.unsplash.com/photo-1707592691247-5c3a1c7ba0e3?auto=format&fit=crop&w=1000&q=85', 'prod-mouse-01', TRUE),
    ('media-mouse-02', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1000&q=85', 'prod-mouse-02', TRUE),
    ('media-mouse-03', 'https://st4.depositphotos.com/1364311/23034/i/450/depositphotos_230349112-stock-photo-wireless-computer-mouse-isolated-white.jpg', 'prod-mouse-03', TRUE),
    ('media-mouse-04', 'https://wallpapers.com/images/hd/black-wired-optical-mouse-wlsw1lu5ehcumx81.png', 'prod-mouse-04', TRUE),
    ('media-mouse-05', 'https://st.depositphotos.com/1004915/2035/i/450/depositphotos_20353239-stock-photo-computer-mouse.jpg', 'prod-mouse-05', TRUE),

    ('media-fan-01', 'https://tiimg.tistatic.com/fp/1/008/516/lightweight-energy-efficient-high-speed-air-cooling-electric-table-fan-587.jpg', 'prod-fan-01', TRUE),
    ('media-fan-02', 'https://cdn.mos.cms.futurecdn.net/V7kXsBgjn37QdPFyFQXDgB.jpg', 'prod-fan-02', TRUE),
    ('media-fan-03', 'https://www.qbicheating.co.uk/media/catalog/category/Desk_Fans.jpg', 'prod-fan-03', TRUE),
    ('media-fan-04', 'https://fs.modenoffice.com/imgRoot/0001/shp/code/2024/09/M770549_500.jpg', 'prod-fan-04', TRUE),
    ('media-fan-05', 'https://www.igenix.co.uk/cdn/shop/files/DF1210_A.jpg?v=1705681027&width=2000', 'prod-fan-05', TRUE),

    ('media-gift-01', 'https://funko.com/on/demandware.static/-/Sites-funko-master-catalog/default/dwef747fbc/images/funko/11496-PX-1MA-1.png', 'prod-gift-01', TRUE),
    ('media-gift-02', 'https://www.popcultcha.com.au/media/catalog/product/cache/207e23213cf636ccdef205098cf3c8a3/f/u/fun86369-01_1.png', 'prod-gift-02', TRUE),
    ('media-gift-03', 'https://www.museumofplay.org/app/uploads/2021/08/rubber-duck-sq.jpg', 'prod-gift-03', TRUE),
    ('media-gift-04', 'https://cdn11.bigcommerce.com/s-nf2x4/products/889/images/9522/yellow-Rubber-Duck-Schanables-2__51940.1568225936.560.850.jpg?c=2', 'prod-gift-04', TRUE),
    ('media-gift-05', 'https://p.globalsources.com/IMAGES/PDT/B1201646078/K5-K9-Crystal-3d-Ball-Night-Lamp.jpg?ver=5796330264', 'prod-gift-05', TRUE),
    ('media-gift-06', 'https://acdn-us.mitiendanube.com/stores/003/229/070/products/d_nq_np_2x_947026-mla77029921814_062024-f-65dae4c8209f5dfba717328374889675-1024-1024.webp', 'prod-gift-06', TRUE),

    ('media-accessory-01', 'https://cdn.dummyjson.com/product-images/sunglasses/black-sun-glasses/thumbnail.webp', 'prod-accessory-01', TRUE),
    ('media-accessory-02', 'https://cdn.dummyjson.com/product-images/sunglasses/classic-sun-glasses/thumbnail.webp', 'prod-accessory-02', TRUE),
    ('media-accessory-03', 'https://cdn.dummyjson.com/product-images/mens-watches/brown-leather-belt-watch/thumbnail.webp', 'prod-accessory-03', TRUE),
    ('media-accessory-04', 'https://cdn.dummyjson.com/product-images/womens-watches/iwc-ingenieur-automatic-steel/thumbnail.webp', 'prod-accessory-04', TRUE)
ON CONFLICT (id) DO NOTHING;

COMMIT;
