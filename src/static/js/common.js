// static/js/forum.js
function formatDateTime(utcTimestamp) {

    try {
        let date = new Date(utcTimestamp);

        if (isNaN(date.getTime())) {
            date = new Date(utcTimestamp + 'Z');
        }

        if (isNaN(date.getTime())) {
            console.error('Invalid date:', utcTimestamp);
            return 'Invalid date';
        }

        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
        };

        return date.toLocaleString(undefined, options);
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Error formatting date';
    }
}

