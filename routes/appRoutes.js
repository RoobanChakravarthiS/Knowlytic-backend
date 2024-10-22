const express = require('express')
const router = express.Router()
const multer = require('multer')
const appController = require('../controllers/appController')
const path = require('path');


const storage = multer.diskStorage({
    destination: './uploads/',
    filename: function (req, file, cb) {
        cb(null, `${file.fieldname}-${Date.now()}${path.extname(file.originalname)}`);
    },
});


const upload = multer({ 
    storage: storage, 
    limits: { fileSize: 5000000 }, // Limit file size to 1MB
});

router.post('/login',appController.login)
router.post('/signup',appController.signup)
router.get('/user/:id',appController.getUser)
router.put('/user/:id', upload.single('profileImage'),appController.updateDetails)
router.post('/achievements/:id', upload.fields([{ name: 'image' }, { name: 'pdf' }]), appController.postAchievement);
router.get('/posts',appController.getPosts)
router.post('/posts/:id/like',appController.likepost)
router.post('/posts/:postId/comment',appController.postComments)
router.get('/posts/:postId/comment',appController.getComments)
router.get('/notifications',appController.getNotifications)
router.post('/generate',appController.generateReport)

module.exports = router