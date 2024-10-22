const {MongoClient} = require('mongodb')
require('dotenv').config();


const uri = process.env.MONGO_URI

async function connectToDatabase() {
    const client = new MongoClient(uri)
    try {
        await client.connect()
        return client
    }
    catch(err) {
        console.log(err)
    }
    finally {
        console.log("Connected to database...")
    }
}

module.exports = {
    connectToDatabase,
    
}
