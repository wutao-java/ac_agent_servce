from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class PrePlaceOrder:
    """订单预提交信息实体。"""

    # count: 课程数量。
    count: int = 0
    # totalAmount: 优惠前的订单总金额，单位为元。
    totalAmount: float = 0.0
    # discountAmount: 订单优惠金额，单位为元。
    discountAmount: float = 0.0
    # couponName: 优惠券规则的展示名称。
    couponName: str = ""
    # payAmount: 优惠后的应付金额，单位为元。
    payAmount: float = 0.0
    # courseIds: 订单包含的课程 ID 列表。
    courseIds: List[str] = field(default_factory=list)
    # orderId: 预订单 ID。
    orderId: Optional[str] = None
    # couponId: 使用的优惠券 ID；无可用优惠券时为 "0"。
    couponId: Optional[str] = None

    @staticmethod
    def of(data: dict[str, Any]) -> "PrePlaceOrder":
        """将预下单接口数据转换为订单预提交信息实体。

        Args:
            data: 预下单接口数据；``totalAmount`` 和优惠金额均以分为单位。

        Returns:
            金额已转换为元的订单预提交信息实体。
        """
        total_amount = round(data.get("totalAmount", 0) / 100, 2)
        discount_amount = 0.0
        coupon_name = ""
        coupon_id = "0"

        discounts = data.get("discounts", [])
        if discounts:
            discount = discounts[0]
            discount_amount = round(
                discount.get("discountAmount", 0) / 100,
                2,
            )
            rules = discount.get("rules", [])
            if len(rules) >= 2:
                coupon_name = f"叠加{len(rules)}券：【优惠{discount_amount}元】"
            else:
                rule = rules[0] if rules else ""
                coupon_name = f"单券：【{rule}】"

            coupon_ids = discount.get("ids", [])
            coupon_id = str(coupon_ids[0]) if coupon_ids else "0"

        courses = data.get("courses", [])
        course_ids = [
            str(course["id"])
            for course in courses
            if course.get("id") is not None
        ]

        return PrePlaceOrder(
            count=len(courses),
            totalAmount=total_amount,
            discountAmount=discount_amount,
            couponName=coupon_name,
            payAmount=round(total_amount - discount_amount, 2),
            courseIds=course_ids,
            orderId=(
                str(data["orderId"])
                if data.get("orderId") is not None
                else None
            ),
            couponId=coupon_id,
        )
