import { ProviderMapper } from '../../../providers/data/mappers/provider.mapper'
import type { CategoryEntity } from '../../domain/entities/category.entity'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'
import type { ProductMediaEntity } from '../../domain/entities/productMedia.entity'
import type { ProductQueryEntity } from '../../domain/entities/productQuery.entity'
import type {
  CategoryDto,
  ProductDetailDto,
  ProductMediaDto,
  ProductQueryInputDto,
} from '../models/product.dto'

export const CategoryMapper = {
  toDomain(dto: CategoryDto): CategoryEntity {
    return {
      id: dto.id,
      name: dto.name,
    }
  },
  toDto(entity: CategoryEntity): CategoryDto {
    return {
      id: entity.id,
      name: entity.name,
    }
  },
}

export const ProductMediaMapper = {
  toDomain(dto: ProductMediaDto): ProductMediaEntity {
    return {
      id: dto.id,
      url: dto.url,
      productId: dto.productId,
      isMain: dto.isMain,
    }
  },
  toDto(entity: ProductMediaEntity): ProductMediaDto {
    return {
      id: entity.id,
      url: entity.url,
      productId: entity.productId,
      isMain: entity.isMain,
    }
  },
}

export const ProductMapper = {
  toDomain(dto: ProductDetailDto): ProductDetailEntity {
    return {
      id: dto.id,
      name: dto.name,
      description: dto.description,
      priceListCents: dto.priceListCents,
      category: CategoryMapper.toDomain(dto.category),
      provider: ProviderMapper.toDomain(dto.provider),
      media: dto.media.map(ProductMediaMapper.toDomain),
    }
  },
  toDto(entity: ProductDetailEntity): ProductDetailDto {
    return {
      id: entity.id,
      name: entity.name,
      description: entity.description,
      priceListCents: entity.priceListCents,
      category: CategoryMapper.toDto(entity.category),
      provider: ProviderMapper.toDto(entity.provider),
      media: entity.media.map(ProductMediaMapper.toDto),
    }
  },
  queryToDto(query: ProductQueryEntity): ProductQueryInputDto {
    return {
      name: query.name ?? null,
      description: query.description ?? null,
      categoryName: query.categoryName ?? null,
      providerName: query.providerName ?? null,
      minPriceCents: query.minPriceCents ?? null,
      maxPriceCents: query.maxPriceCents ?? null,
      limit: query.limit ?? null,
      offset: query.offset ?? null,
    }
  },
}
