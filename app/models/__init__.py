# 统一导出所有模型，外部 import 无需修改路径
from app.models.base import User, Family, FamilyMember  # noqa: F401
from app.models.plant import Plant, WateringRecord  # noqa: F401
from app.models.vocab import (  # noqa: F401
    Child, WordBook, Word,
    DictationSession, DictationResult, MistakeRecord,
    OCRTask,
)
from app.models.shopping import ShoppingList, ShoppingItem, FrequentItem  # noqa: F401
from app.models.cooking import Recipe, RecipeIngredient, RecipeStep, RecipeFavorite  # noqa: F401
