import { MercadoPagoConfig, Preference } from 'mercadopago'

const MP_ACCESS_TOKEN = process.env.MP_TOKEN;
 
export const createOrder = async (req, res) => {
const client = new MercadoPagoConfig({accessToken: MP_ACCESS_TOKEN})

const preference = new Preference(client)

try {
   const response = await preference.create({
        body: {
           ...req.body,
            redirect_urls: {
                success: 'https://www.mercadopago.com.ar/mp-assets/img/success.png',
                failure: 'https://www.mercadopago.com.ar/mp-assets/img/failure.png',
                pending: 'https://www.mercadopago.com.ar/mp-assets/img/pending.png'
            },
        }
    })
    res.json(response)
    console.log(response)
}
catch (error) {
    console.log(error)
}}