
// Set storage engine

// Initialize upload
// Adjust maxCount as needed

// Check file type
function checkFileType(file, cb) {
    const filetypes = /jpeg|jpg|png|pdf/; // Allowed file types
    const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = filetypes.test(file.mimetype);
    
    if (mimetype && extname) {
        return cb(null, true);
    } else {
        cb('Error: Images and PDFs Only!'); // Customize the error message as needed
    }
}

module.exports = upload; // Export the upload middleware
