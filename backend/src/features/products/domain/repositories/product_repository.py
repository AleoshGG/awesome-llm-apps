from abc import ABC, abstractmethod

from ..entities.product_entity import Product

class ProductRepository(ABC):
    @abstractmethod
    async def find_all() -> list[Product]: pass 

    #@abstractmethod
    #async def find_by_quiere() -> list[Product]: pass #Pasar objeto quiere