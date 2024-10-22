function generateId(length = 16) {
    const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*_-'
    const charactersLength = characters.length
    return Array.from({ length }, () =>
        characters.charAt(Math.floor(Math.random() * charactersLength))
    ).join('')
}

module.exports = {
    generateId
}