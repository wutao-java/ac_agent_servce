import unittest

from agent.tianji.tools.result import CourseInfo, PrePlaceOrder


class CourseInfoTest(unittest.TestCase):

    def test_of_converts_price_from_cents_to_yuan(self):
        course = CourseInfo.of({
            "id": "course-1",
            "name": "Java课程",
            "price": 19900,
            "validDuration": 999,
            "usePeople": "Java开发者",
            "detail": "课程详情",
        })

        self.assertEqual(course.id, "course-1")
        self.assertEqual(course.price, 199.0)


class PrePlaceOrderTest(unittest.TestCase):

    def test_of_uses_best_discount_and_builds_frontend_card_data(self):
        order = PrePlaceOrder.of({
            "orderId": "order-1",
            "totalAmount": 19900,
            "discounts": [{
                "ids": ["coupon-1", "coupon-2"],
                "rules": ["优惠3元", "优惠3元"],
                "discountAmount": 600,
            }],
            "courses": [{
                "id": "course-1",
                "name": "Java课程",
                "price": 19900,
            }],
        })

        self.assertEqual(order.count, 1)
        self.assertEqual(order.totalAmount, 199.0)
        self.assertEqual(order.discountAmount, 6.0)
        self.assertEqual(order.payAmount, 193.0)
        self.assertEqual(order.courseIds, ["course-1"])
        self.assertEqual(order.couponId, "coupon-1")
        self.assertEqual(order.couponName, "叠加2券：【优惠6.0元】")


if __name__ == "__main__":
    unittest.main()
