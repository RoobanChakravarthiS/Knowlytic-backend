const express = require('express');
const cors = require('cors');
const appRoutes = require('./routes/appRoutes')
require('dotenv').config();
const path = require('path');
const corsOptions = {
    origin: '*', 
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
};
const app = express();
app.use(express.json());
app.use(cors(corsOptions));
app.use('/', appRoutes);
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0',() => {
    console.log(`Server is running on port ${PORT}`);
});
 