import express from 'express'
import morgan from 'morgan'
import path from 'path'

const app = express()

app.use(morgan('dev'))
app.use(express.static(path.resolve('public')))

app.listen(3000, () => {
    console.log("🚀 Servidor escuchando en http://localhost:3000");
  });