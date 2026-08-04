from django.conf import settings

def get_gateway_checkout_url(request, gateway_token, invoice_id):
    """
    Constructs the redirect URL for checkout gateway sessions.
    If PAYMENT_GATEWAY_CHECKOUT_URL is defined, it will format and return it.
    If MOCK_GATEWAY_ENABLED is True, it returns the absolute local mock checkout URL.
    Otherwise, it defaults to the mock-pg.com fallback.
    """
    base_url = getattr(settings, 'PAYMENT_GATEWAY_CHECKOUT_URL', None)
    if base_url:
        return base_url.format(token=gateway_token, invoice_id=invoice_id)

    if getattr(settings, 'MOCK_GATEWAY_ENABLED', False):
        proto = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        
        # Preserve XTransformPort query parameter to route correctly via Caddy in previews
        transform_port = request.GET.get('XTransformPort')
        query_params = f"?invoice={invoice_id}"
        if transform_port:
            query_params += f"&XTransformPort={transform_port}"
            
        return f"{proto}://{host}/mock-checkout/{gateway_token}{query_params}"

    return f"https://mock-pg.com/checkout/{gateway_token}?invoice={invoice_id}"
