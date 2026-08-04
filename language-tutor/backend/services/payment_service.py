import stripe

from config import settings
from database.enums import SubscriptionTier
from database.models import User


class PaymentService:
    TIERS = {
        SubscriptionTier.FREE: {"price_id": None, "messages_per_day": 10},
        SubscriptionTier.BASIC: {"price_id": "price_basic", "messages_per_day": 100},
        SubscriptionTier.PREMIUM: {"price_id": "price_premium", "messages_per_day": -1},
    }

    def __init__(self) -> None:
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    def get_daily_limit(self, user: User) -> int:
        tier_info = self.TIERS.get(user.subscription_tier, self.TIERS[SubscriptionTier.FREE])
        return tier_info["messages_per_day"]

    async def create_checkout_session(self, user: User, tier: SubscriptionTier, success_url: str, cancel_url: str) -> str | None:
        if not settings.stripe_secret_key:
            return None

        tier_info = self.TIERS.get(tier)
        if not tier_info or not tier_info["price_id"]:
            return None

        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            customer_email=None if user.stripe_customer_id else f"user_{user.telegram_id}@language-tutor.app",
            payment_method_types=["card"],
            line_items=[{"price": tier_info["price_id"], "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"telegram_id": str(user.telegram_id), "tier": tier.value},
        )
        return session.url

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict | None:
        if not settings.stripe_webhook_secret:
            return None
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
            return event
        except (ValueError, stripe.error.SignatureVerificationError):
            return None


payment_service = PaymentService()
