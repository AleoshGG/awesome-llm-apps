import { ProductMapper } from '../../../products/data/mappers/product.mapper'
import type { CartItemEntity } from '../../domain/entities/cartItem.entity'
import type { SaleEntity } from '../../domain/entities/sale.entity'
import type { SaleItemEntity } from '../../domain/entities/saleItem.entity'
import type { CartItemDto, SaleDto, SaleItemDto } from '../models/sales.dto'

export const CartMapper = {
  toDomain(dto: CartItemDto): CartItemEntity {
    return {
      product: ProductMapper.toDomain(dto.product),
      quantity: dto.quantity,
    }
  },
  toDto(entity: CartItemEntity): CartItemDto {
    return {
      product: ProductMapper.toDto(entity.product),
      quantity: entity.quantity,
    }
  },
}

export const SaleItemMapper = {
  toDomain(dto: SaleItemDto): SaleItemEntity {
    return {
      product: ProductMapper.toDomain(dto.product),
      quantity: dto.quantity,
    }
  },
  toDto(entity: SaleItemEntity): SaleItemDto {
    return {
      product: ProductMapper.toDto(entity.product),
      quantity: entity.quantity,
    }
  },
}

export const SaleMapper = {
  toDomain(dto: SaleDto): SaleEntity {
    return {
      id: dto.id,
      createdAt: dto.createdAt,
      items: dto.items.map(SaleItemMapper.toDomain),
    }
  },
  toDto(entity: SaleEntity): SaleDto {
    return {
      id: entity.id,
      createdAt: entity.createdAt,
      items: entity.items.map(SaleItemMapper.toDto),
    }
  },
}
