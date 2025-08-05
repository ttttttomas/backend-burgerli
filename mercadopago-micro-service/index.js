import express from 'express'
import morgan from 'morgan'
import path from 'path'
import routes from './routes/routes.js'
import cors from 'cors';

const app = express()

app.use(morgan('dev'))
app.use(express.json()); 
app.use(cors({
    origin: 'http://localhost:3001',
    methods: ['*'],
    allowedHeaders: ['*'],
    credentials: true,
}))
app.use(express.static(path.resolve('public')))

app.use('/', routes)

app.listen(3000, () => {
    console.log("🚀 Servidor escuchando en http://localhost:3000");
});