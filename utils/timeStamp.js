function timeStampGenerator() {
    const now = new Date();
    const timestamp = now.getFullYear() + '-' +
                      ('0' + (now.getMonth() + 1)).slice(-2) + '-' +
                      ('0' + now.getDate()).slice(-2) + ' ' +
                      ('0' + now.getHours()).slice(-2) + ':' +
                      ('0' + now.getMinutes()).slice(-2) + ':' +
                      ('0' + now.getSeconds()).slice(-2)
    return timestamp
}

module.exports = {
    timeStampGenerator
}