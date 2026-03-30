import json
import os
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, ShoppingList, ShoppingItem, FrequentItem
from app.auth import get_current_user
from app.schemas import (
    ShoppingItemCreate,
    ShoppingItemBatchCreate,
    ShoppingItemUpdate,
    ShoppingItemOut,
    ShoppingListOut,
    ShoppingHistoryOut,
    FrequentItemOut,
    FrequentAddToListRequest,
)

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


def _get_family_id(current_user: User) -> int:
    """获取当前用户的活跃家庭 ID"""
    if not current_user.current_family_id:
        raise HTTPException(status_code=400, detail="请先加入或创建一个家庭")
    return current_user.current_family_id


def _get_or_create_active_list(db: Session, family_id: int) -> ShoppingList:
    """获取当前家庭的活跃清单，没有则自动创建"""
    stmt = select(ShoppingList).where(
        ShoppingList.family_id == family_id,
        ShoppingList.status == "active",
    )
    sl = db.scalars(stmt).first()
    if not sl:
        sl = ShoppingList(family_id=family_id)
        db.add(sl)
        db.commit()
        db.refresh(sl)
    return sl


def _build_item_out(item: ShoppingItem) -> dict:
    """构建带有 buyer_name / creator_name 的输出"""
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "price": item.price,
        "category": item.category,
        "note": item.note,
        "is_bought": item.is_bought,
        "bought_by": item.bought_by,
        "bought_at": item.bought_at,
        "buyer_name": item.buyer.nickname if item.buyer else "",
        "created_by": item.created_by,
        "creator_name": item.creator.nickname if item.creator else "",
        "created_at": item.created_at,
    }


def _update_frequent(db: Session, family_id: int, name: str, category: str):
    """更新常买商品统计"""
    freq = db.scalars(
        select(FrequentItem).where(
            FrequentItem.family_id == family_id,
            FrequentItem.name == name,
        )
    ).first()
    if freq:
        freq.buy_count += 1
        freq.last_bought_at = datetime.now()
    else:
        freq = FrequentItem(
            family_id=family_id,
            name=name,
            category=category,
            buy_count=1,
        )
        db.add(freq)


# ---- 获取当前清单 ----

@router.get("/current", response_model=ShoppingListOut)
def get_current_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前活跃清单（含全部商品）"""
    family_id = _get_family_id(current_user)
    sl = _get_or_create_active_list(db, family_id)
    items = (
        db.scalars(
            select(ShoppingItem)
            .where(ShoppingItem.list_id == sl.id)
            .order_by(ShoppingItem.is_bought, ShoppingItem.created_at.desc())
        )
        .all()
    )
    return {
        "id": sl.id,
        "name": sl.name,
        "status": sl.status,
        "created_at": sl.created_at,
        "items": [_build_item_out(i) for i in items],
    }


# ---- 添加商品（支持批量） ----

@router.post("/items", response_model=List[ShoppingItemOut], status_code=201)
def add_items(
    data: ShoppingItemBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加商品到当前清单，支持批量"""
    family_id = _get_family_id(current_user)
    sl = _get_or_create_active_list(db, family_id)
    created = []
    for item_data in data.items:
        item = ShoppingItem(
            list_id=sl.id,
            name=item_data.name.strip(),
            quantity=item_data.quantity,
            price=item_data.price,
            category=item_data.category.value,
            note=item_data.note,
            created_by=current_user.id,
        )
        db.add(item)
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return [_build_item_out(i) for i in created]


# ---- 编辑商品 ----

@router.put("/items/{item_id}", response_model=ShoppingItemOut)
def update_item(
    item_id: int,
    data: ShoppingItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    item = _get_item(db, item_id, family_id)
    update_data = data.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value
    for key, val in update_data.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return _build_item_out(item)


# ---- 删除商品 ----

@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    item = _get_item(db, item_id, family_id)
    db.delete(item)
    db.commit()


# ---- 标记已买 ----

@router.put("/items/{item_id}/buy", response_model=ShoppingItemOut)
def buy_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    item = _get_item(db, item_id, family_id)
    item.is_bought = True
    item.bought_by = current_user.id
    item.bought_at = datetime.now()
    # 更新常买统计
    _update_frequent(db, family_id, item.name, item.category)
    db.commit()
    db.refresh(item)
    return _build_item_out(item)


# ---- 取消已买 ----

@router.put("/items/{item_id}/unbuy", response_model=ShoppingItemOut)
def unbuy_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    item = _get_item(db, item_id, family_id)
    item.is_bought = False
    item.bought_by = None
    item.bought_at = None
    db.commit()
    db.refresh(item)
    return _build_item_out(item)


# ---- 归档当前清单（清空已买） ----

@router.post("/archive")
def archive_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归档已买商品，未买商品保留在新清单中"""
    family_id = _get_family_id(current_user)
    sl = _get_or_create_active_list(db, family_id)

    all_items = db.scalars(
        select(ShoppingItem).where(ShoppingItem.list_id == sl.id)
    ).all()
    unbought = [i for i in all_items if not i.is_bought]
    bought = [i for i in all_items if i.is_bought]

    if not bought:
        raise HTTPException(status_code=400, detail="没有已买的商品可以归档")

    sl.status = "archived"
    sl.archived_at = datetime.now()

    new_list = ShoppingList(family_id=family_id)
    db.add(new_list)
    db.flush()
    for item in unbought:
        item.list_id = new_list.id
    db.commit()

    return {"message": f"已归档 {len(bought)} 件商品", "new_list_id": new_list.id}


# ---- AI 智能拆分添加 ----

class SmartAddRequest(BaseModel):
    text: str  # 用户输入的自然语言，如"明天做红烧肉需要什么"


class SmartAddItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    category: str = "other"


class SmartAddResponse(BaseModel):
    items: List[SmartAddItem]


@router.post("/smart-add", response_model=SmartAddResponse)
def smart_add(
    req: SmartAddRequest,
    current_user: User = Depends(get_current_user),
):
    """AI 智能拆分：输入一句话，返回拆解后的商品列表"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未配置 DASHSCOPE_API_KEY")

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    try:
        resp = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个购物助手。用户会用自然语言描述他们需要买什么，你要把它拆解为具体的商品列表。\n"
                        "返回 JSON 格式（不要 markdown 代码块），结构为：\n"
                        '{"items": [{"name": "商品名", "quantity": "数量（如2斤、1盒，可为null）", '
                        '"category": "分类"}]}\n'
                        "分类只能是以下之一：fresh(生鲜果蔬)、meat(肉禽蛋奶)、grain(粮油调味)、"
                        "snack(零食饮料)、daily(日用百货)、other(其他)\n"
                        "只返回 JSON，不要其他内容。"
                    ),
                },
                {"role": "user", "content": req.text},
            ],
        )
        content = resp.choices[0].message.content.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            raise ValueError(f"AI 返回内容无法解析: {content}")
        result = json.loads(json_match.group())
        items = []
        for item in result.get("items", []):
            cat = item.get("category", "other")
            if cat not in ("fresh", "meat", "grain", "snack", "daily", "other"):
                cat = "other"
            items.append(SmartAddItem(
                name=item.get("name", ""),
                quantity=item.get("quantity"),
                category=cat,
            ))
        return SmartAddResponse(items=items)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 拆分失败：{str(e)}")


# ---- 历史记录 ----

@router.get("/history", response_model=List[ShoppingHistoryOut])
def list_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取已归档的购物清单列表"""
    family_id = _get_family_id(current_user)
    lists = db.scalars(
        select(ShoppingList)
        .where(ShoppingList.family_id == family_id, ShoppingList.status == "archived")
        .order_by(ShoppingList.archived_at.desc())
        .limit(50)
    ).all()
    result = []
    for sl in lists:
        items = db.scalars(
            select(ShoppingItem).where(ShoppingItem.list_id == sl.id)
        ).all()
        total_price = sum(i.price for i in items if i.price) or None
        result.append({
            "id": sl.id,
            "name": sl.name,
            "archived_at": sl.archived_at,
            "item_count": len(items),
            "total_price": total_price,
            "items": [_build_item_out(i) for i in items],
        })
    return result


@router.get("/history/{list_id}", response_model=ShoppingHistoryOut)
def get_history_detail(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取某次历史清单详情"""
    family_id = _get_family_id(current_user)
    sl = db.get(ShoppingList, list_id)
    if not sl or sl.family_id != family_id or sl.status != "archived":
        raise HTTPException(status_code=404, detail="历史记录不存在")
    items = db.scalars(
        select(ShoppingItem).where(ShoppingItem.list_id == sl.id)
    ).all()
    total_price = sum(i.price for i in items if i.price) or None
    return {
        "id": sl.id,
        "name": sl.name,
        "archived_at": sl.archived_at,
        "item_count": len(items),
        "total_price": total_price,
        "items": [_build_item_out(i) for i in items],
    }


@router.post("/history/{list_id}/rebuy")
def rebuy_history(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一键重买：将历史清单中的商品重新加入当前清单"""
    family_id = _get_family_id(current_user)
    sl = db.get(ShoppingList, list_id)
    if not sl or sl.family_id != family_id or sl.status != "archived":
        raise HTTPException(status_code=404, detail="历史记录不存在")

    active_list = _get_or_create_active_list(db, family_id)
    old_items = db.scalars(
        select(ShoppingItem).where(ShoppingItem.list_id == sl.id)
    ).all()

    count = 0
    for old in old_items:
        new_item = ShoppingItem(
            list_id=active_list.id,
            name=old.name,
            quantity=old.quantity,
            price=old.price,
            category=old.category,
            note=old.note,
            created_by=current_user.id,
        )
        db.add(new_item)
        count += 1
    db.commit()
    return {"message": f"已添加 {count} 件商品到当前清单"}


# ---- 常买商品 ----

@router.get("/frequent", response_model=List[FrequentItemOut])
def list_frequent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取常买商品列表（按购买次数降序）"""
    family_id = _get_family_id(current_user)
    items = db.scalars(
        select(FrequentItem)
        .where(FrequentItem.family_id == family_id)
        .order_by(FrequentItem.buy_count.desc())
        .limit(50)
    ).all()
    return items


@router.post("/frequent/add-to-list")
def frequent_add_to_list(
    data: FrequentAddToListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将常买商品加入当前清单"""
    family_id = _get_family_id(current_user)
    active_list = _get_or_create_active_list(db, family_id)

    freq_items = db.scalars(
        select(FrequentItem).where(
            FrequentItem.id.in_(data.item_ids),
            FrequentItem.family_id == family_id,
        )
    ).all()

    count = 0
    for fi in freq_items:
        new_item = ShoppingItem(
            list_id=active_list.id,
            name=fi.name,
            category=fi.category,
            created_by=current_user.id,
        )
        db.add(new_item)
        count += 1
    db.commit()
    return {"message": f"已添加 {count} 件商品到当前清单"}


@router.delete("/frequent/{item_id}", status_code=204)
def delete_frequent(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除常买商品"""
    family_id = _get_family_id(current_user)
    fi = db.get(FrequentItem, item_id)
    if not fi or fi.family_id != family_id:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(fi)
    db.commit()


# ---- 辅助函数 ----

def _get_item(db: Session, item_id: int, family_id: int) -> ShoppingItem:
    """获取商品并验证归属家庭"""
    item = db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    sl = db.get(ShoppingList, item.list_id)
    if not sl or sl.family_id != family_id:
        raise HTTPException(status_code=404, detail="商品不存在")
    return item
