async function lose() {
    try {
        const response = await fetch('/api/lose', {
            method: 'DELETE',
        });

        const statusCode = response.status;
        const data = await response.json();
        return {
            statusCode,
            data,
        };
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        return {
            statusCode: 500,
            data: { msg: 'Ошибка сервера' },
        };
    }
}


async function get_flag() {
    try {
        const response = await fetch('/api/flag', {
            method: 'GET',
        });

        const statusCode = response.status;
        const data = await response.json();
        return {
            statusCode,
            data,
        };
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        return {
            statusCode: 500,
            data: { msg: 'Ошибка сервера' },
        };
    }
}