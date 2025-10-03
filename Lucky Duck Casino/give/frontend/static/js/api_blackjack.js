async function set_bet_and_double(endpoint, bet, name_field) {
    try {
        const response = await fetch(`${endpoint}?${name_field}=${bet}`, {
            method: 'POST',
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

async function api_get_put(endpoint, method) {
    try {
        const response = await fetch(endpoint, {
            method: method,
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


