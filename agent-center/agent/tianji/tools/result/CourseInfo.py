from dataclasses import dataclass
from typing import Optional


@dataclass
class CourseInfo:
    """课程信息实体。"""

    id: Optional[str] = None
    name: Optional[str] = None
    price: float = 0.0
    validDuration: Optional[int] = None
    usePeople: Optional[str] = None
    detail: Optional[str] = None

    @staticmethod
    def of(data: dict) -> Optional["CourseInfo"]:
        if data is None:
            return None

        raw_price = data.get("price")
        return CourseInfo(
            id=str(data["id"]) if data.get("id") is not None else None,
            name=data.get("name"),
            price=round(raw_price / 100, 2) if raw_price is not None else 0.0,
            validDuration=data.get("validDuration"),
            usePeople=data.get("usePeople"),
            detail=data.get("detail"),
        )
