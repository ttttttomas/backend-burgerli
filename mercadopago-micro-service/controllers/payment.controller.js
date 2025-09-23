import { MercadoPagoConfig, Preference } from 'mercadopago'

const MP_ACCESS_TOKEN = process.env.MP_TOKEN;
 
export const createOrder = async (req, res) => {
   try {
    const client = new MercadoPagoConfig({ accessToken: MP_ACCESS_TOKEN });
    const preference = new Preference(client);

    const items = Array.isArray(req.body?.items) ? req.body.items : [];
    if (!items.length || items[0]?.unit_price == null) {
      return res.status(400).json({ error: true, message: "unit_price needed" });
    }

    const pref = await preference.create({
      body: {
        items: items.map((it) => ({
          id: it.id ?? "sku-1",
          title: it.title ?? "Compra en Burgerli",
          description: it.description ?? "Sin descripción",
          quantity: Number(it.quantity ?? 1),
          unit_price: Number(it.unit_price),
          currency_id: it.currency_id ?? "ARS",
          category_id: it.category_id ?? "general",
          picture_url: it.picture_url,
        })),
        back_urls: {
          success: "http://localhost:3000/success",
          failure: "http://localhost:3000/failure",
          pending: "http://localhost:3000/pending",
        },
        auto_return: "approved",
        binary_mode: true,
        notification_url: "http://localhost:3000/api/mercadopago/webhook",
        external_reference: `order_${Date.now()}`,
      },
    });

    return res.json({
      id: pref.id,
      init_point: pref.init_point,
      sandbox_init_point: pref.sandbox_init_point,
    });
  }catch (error) {
    console.error("MP create preference error:", error);
    return res.status(500).json({ error: true, message: error?.message ?? "Error" });
}}
