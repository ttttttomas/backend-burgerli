import { MercadoPagoConfig, Preference } from 'mercadopago'

const MP_ACCESS_TOKEN = process.env.MP_TOKEN;
 
export const createOrder = async (req, res) => {
  try {
    const client = new MercadoPagoConfig({ accessToken: MP_ACCESS_TOKEN });
    const preference = new Preference(client);

    const pref = await preference.create({
      body: {
        items: [
          {
            id: "sku-1",
            title: "Compra en Burgerli",
            description: req.body?.description ?? "Sin descripción",
            quantity: req.body?.quantity ?? 1,
            unit_price: req.body?.unit_price,
            currency_id: "ARS",
            category_id: req.body?.category_id ?? "general",
            picture_url: req.body?.picture_url,
          },
        ],
        back_urls: {
          success: "http://localhost:3000/success",
          failure: "/",
          pending: "/",
        },
        auto_return: "approved",
        binary_mode: true,
        notification_url: "http://localhost:3000/api/mercadopago/webhook",
        external_reference: `order_${Date.now()}`
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
