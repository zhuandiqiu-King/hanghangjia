"""烹饪助手 API"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    User, Recipe, RecipeIngredient, RecipeStep, RecipeFavorite,
    ShoppingList, ShoppingItem,
)
from app.schemas import (
    RecipeListOut, RecipeDetailOut, RecipeCreateRequest, RecipeUpdateRequest,
    RecipeIngredientOut, RecipeStepOut, CookingAddToShoppingRequest,
)

router = APIRouter(prefix="/api/cooking", tags=["cooking"])


CATEGORY_MAP = {
    "home": "家常菜",
    "quick": "快手菜",
    "soup": "汤羹",
    "breakfast": "早餐",
    "cold": "凉菜",
    "baking": "烘焙",
    "baby": "宝宝餐",
    "diet": "减脂餐",
}


def _get_family_id(current_user: User) -> int:
    if not current_user.current_family_id:
        raise HTTPException(status_code=400, detail="请先加入或创建一个家庭")
    return current_user.current_family_id


def _build_recipe_list_item(recipe: Recipe, favorited_ids: set) -> dict:
    return {
        "id": recipe.id,
        "name": recipe.name,
        "cover_image": recipe.cover_image,
        "description": recipe.description,
        "cook_time": recipe.cook_time,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "category": recipe.category,
        "tags": recipe.tags,
        "source": recipe.source,
        "favorite_count": recipe.favorite_count,
        "is_favorited": recipe.id in favorited_ids,
        "created_at": recipe.created_at,
    }


def _get_user_favorited_ids(db: Session, user_id: int) -> set:
    stmt = select(RecipeFavorite.recipe_id).where(RecipeFavorite.user_id == user_id)
    return set(db.scalars(stmt).all())


# ========== 菜谱浏览 ==========

@router.get("/categories")
def get_categories():
    """获取菜谱分类列表"""
    return [{"id": k, "name": v} for k, v in CATEGORY_MAP.items()]


@router.get("/recipes", response_model=list[RecipeListOut])
def list_recipes(
    keyword: Optional[str] = Query(None, max_length=50),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    max_time: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """菜谱列表（支持搜索、分类筛选、分页）"""
    family_id = _get_family_id(current_user)

    # 公开菜谱 + 本家庭菜谱
    stmt = select(Recipe).where(
        or_(Recipe.is_public == True, Recipe.family_id == family_id)
    )

    if keyword:
        # 搜索菜名或食材名
        ingredient_recipe_ids = select(RecipeIngredient.recipe_id).where(
            RecipeIngredient.name.contains(keyword)
        ).scalar_subquery()
        stmt = stmt.where(
            or_(
                Recipe.name.contains(keyword),
                Recipe.id.in_(ingredient_recipe_ids),
            )
        )
    if category:
        stmt = stmt.where(Recipe.category == category)
    if difficulty:
        stmt = stmt.where(Recipe.difficulty == difficulty)
    if max_time:
        stmt = stmt.where(Recipe.cook_time <= max_time)

    stmt = stmt.order_by(Recipe.favorite_count.desc(), Recipe.id.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    recipes = db.scalars(stmt).all()
    favorited_ids = _get_user_favorited_ids(db, current_user.id)

    return [_build_recipe_list_item(r, favorited_ids) for r in recipes]


@router.get("/recipes/{recipe_id}", response_model=RecipeDetailOut)
def get_recipe_detail(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """菜谱详情"""
    family_id = _get_family_id(current_user)

    stmt = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients), selectinload(Recipe.steps))
        .where(Recipe.id == recipe_id)
    )
    recipe = db.scalars(stmt).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")

    # 权限检查：公开菜谱或本家庭菜谱
    if not recipe.is_public and recipe.family_id != family_id:
        raise HTTPException(status_code=403, detail="无权查看此菜谱")

    favorited_ids = _get_user_favorited_ids(db, current_user.id)

    # 获取创建者昵称
    creator_name = ""
    if recipe.created_by:
        creator = db.get(User, recipe.created_by)
        if creator:
            creator_name = creator.nickname

    # 食材按 sort_order 排序
    ingredients = sorted(recipe.ingredients, key=lambda i: i.sort_order)
    # 步骤按 step_number 排序
    steps = sorted(recipe.steps, key=lambda s: s.step_number)

    return {
        "id": recipe.id,
        "name": recipe.name,
        "cover_image": recipe.cover_image,
        "description": recipe.description,
        "cook_time": recipe.cook_time,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "category": recipe.category,
        "tags": recipe.tags,
        "tips": recipe.tips,
        "source": recipe.source,
        "favorite_count": recipe.favorite_count,
        "is_favorited": recipe.id in favorited_ids,
        "created_at": recipe.created_at,
        "creator_name": creator_name,
        "ingredients": [
            {
                "id": ing.id,
                "name": ing.name,
                "amount": ing.amount,
                "group_name": ing.group_name,
                "sort_order": ing.sort_order,
            }
            for ing in ingredients
        ],
        "steps": [
            {
                "id": s.id,
                "step_number": s.step_number,
                "content": s.content,
                "tip": s.tip,
                "image_url": s.image_url,
            }
            for s in steps
        ],
    }


# ========== 收藏管理 ==========

@router.get("/favorites", response_model=list[RecipeListOut])
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """我的收藏列表"""
    stmt = (
        select(Recipe)
        .join(RecipeFavorite, RecipeFavorite.recipe_id == Recipe.id)
        .where(RecipeFavorite.user_id == current_user.id)
        .order_by(RecipeFavorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    recipes = db.scalars(stmt).all()
    favorited_ids = _get_user_favorited_ids(db, current_user.id)
    return [_build_recipe_list_item(r, favorited_ids) for r in recipes]


@router.post("/favorites/{recipe_id}", status_code=201)
def add_favorite(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """收藏菜谱"""
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")

    # 检查是否已收藏
    stmt = select(RecipeFavorite).where(
        RecipeFavorite.user_id == current_user.id,
        RecipeFavorite.recipe_id == recipe_id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        return {"detail": "已收藏"}

    fav = RecipeFavorite(user_id=current_user.id, recipe_id=recipe_id)
    db.add(fav)
    recipe.favorite_count += 1
    db.commit()
    return {"detail": "收藏成功"}


@router.delete("/favorites/{recipe_id}", status_code=200)
def remove_favorite(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消收藏"""
    stmt = select(RecipeFavorite).where(
        RecipeFavorite.user_id == current_user.id,
        RecipeFavorite.recipe_id == recipe_id,
    )
    fav = db.scalars(stmt).first()
    if not fav:
        raise HTTPException(status_code=404, detail="未收藏此菜谱")

    db.delete(fav)
    recipe = db.get(Recipe, recipe_id)
    if recipe and recipe.favorite_count > 0:
        recipe.favorite_count -= 1
    db.commit()
    return {"detail": "已取消收藏"}


# ========== 家庭菜谱 ==========

@router.get("/family-recipes", response_model=list[RecipeListOut])
def list_family_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """家庭菜谱列表"""
    family_id = _get_family_id(current_user)
    stmt = (
        select(Recipe)
        .where(Recipe.family_id == family_id, Recipe.source == "family")
        .order_by(Recipe.created_at.desc())
    )
    recipes = db.scalars(stmt).all()
    favorited_ids = _get_user_favorited_ids(db, current_user.id)
    return [_build_recipe_list_item(r, favorited_ids) for r in recipes]


@router.post("/family-recipes", status_code=201, response_model=RecipeDetailOut)
def create_family_recipe(
    req: RecipeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建家庭菜谱"""
    family_id = _get_family_id(current_user)

    recipe = Recipe(
        name=req.name,
        cover_image=req.cover_image,
        description=req.description,
        cook_time=req.cook_time,
        servings=req.servings,
        difficulty=req.difficulty.value,
        category=req.category.value,
        tips=req.tips,
        source="family",
        family_id=family_id,
        created_by=current_user.id,
        is_public=False,
    )
    db.add(recipe)
    db.flush()  # 获取 recipe.id

    # 添加食材
    for i, ing in enumerate(req.ingredients):
        db.add(RecipeIngredient(
            recipe_id=recipe.id,
            name=ing.name,
            amount=ing.amount,
            group_name=ing.group_name,
            sort_order=i,
        ))

    # 添加步骤
    for step in req.steps:
        db.add(RecipeStep(
            recipe_id=recipe.id,
            step_number=step.step_number,
            content=step.content,
            tip=step.tip,
        ))

    db.commit()
    db.refresh(recipe)

    # 返回详情
    return get_recipe_detail(recipe.id, db, current_user)


@router.put("/family-recipes/{recipe_id}", response_model=RecipeDetailOut)
def update_family_recipe(
    recipe_id: int,
    req: RecipeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑家庭菜谱"""
    family_id = _get_family_id(current_user)

    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    if recipe.source != "family" or recipe.family_id != family_id:
        raise HTTPException(status_code=403, detail="无权编辑此菜谱")

    # 更新基本字段
    update_data = req.model_dump(exclude_unset=True, exclude={"ingredients", "steps"})
    for key, val in update_data.items():
        if val is not None:
            setattr(recipe, key, val.value if hasattr(val, "value") else val)

    # 更新食材（全量替换）
    if req.ingredients is not None:
        for old in recipe.ingredients:
            db.delete(old)
        db.flush()
        for i, ing in enumerate(req.ingredients):
            db.add(RecipeIngredient(
                recipe_id=recipe.id,
                name=ing.name,
                amount=ing.amount,
                group_name=ing.group_name,
                sort_order=i,
            ))

    # 更新步骤（全量替换）
    if req.steps is not None:
        for old in recipe.steps:
            db.delete(old)
        db.flush()
        for step in req.steps:
            db.add(RecipeStep(
                recipe_id=recipe.id,
                step_number=step.step_number,
                content=step.content,
                tip=step.tip,
            ))

    db.commit()
    db.refresh(recipe)
    return get_recipe_detail(recipe.id, db, current_user)


@router.delete("/family-recipes/{recipe_id}", status_code=200)
def delete_family_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除家庭菜谱"""
    family_id = _get_family_id(current_user)

    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    if recipe.source != "family" or recipe.family_id != family_id:
        raise HTTPException(status_code=403, detail="无权删除此菜谱")

    db.delete(recipe)
    db.commit()
    return {"detail": "已删除"}


# ========== 食材加入购物清单 ==========

@router.post("/add-to-shopping", status_code=201)
def add_to_shopping(
    req: CookingAddToShoppingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """菜谱食材批量加入购物清单"""
    family_id = _get_family_id(current_user)

    # 获取或创建活跃购物清单
    stmt = select(ShoppingList).where(
        ShoppingList.family_id == family_id,
        ShoppingList.status == "active",
    )
    sl = db.scalars(stmt).first()
    if not sl:
        sl = ShoppingList(family_id=family_id)
        db.add(sl)
        db.flush()

    added = 0
    for item in req.items:
        db.add(ShoppingItem(
            list_id=sl.id,
            name=item.name,
            quantity=item.quantity,
            category=item.category.value if item.category else "other",
            created_by=current_user.id,
        ))
        added += 1

    db.commit()
    return {"detail": f"已添加 {added} 项到购物清单"}
