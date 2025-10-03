async function authenticate(endpoint, username, password) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
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

