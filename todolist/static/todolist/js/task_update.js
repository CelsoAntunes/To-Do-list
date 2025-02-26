function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            cookieValue = cookie.substring('csrftoken='.length, cookie.length);
            break;
        }
    }
    return cookieValue;
}

$(document).ready(function() {

    $(".task-checkbox").on('change', function() {
        var taskId = $(this).data('task-id');
        var isChecked = $(this).prop('checked');

        console.log("Sending request:", {
            url: updateTaskURL,
            task_id: taskId,
            done: isChecked,
            csrf_token: getCSRFToken()
        });

        $.ajax({
            url: updateTaskURL,  
            method: "POST",
            headers: { "X-CSRFToken": getCSRFToken() }, 
            data: {
                task_id: taskId,
                done: isChecked
            },
            success: function(response) {
                console.log('Task updated successfully', response);
            },
            error: function(xhr, status, error) {
                console.error('Error updating task', xhr.responseText);
            }
        });
    });
});