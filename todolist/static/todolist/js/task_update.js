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
    $(".editable-task").on("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
        }
    });
    $(".delete-task").on('click', function(e) {
        e.stopPropagation();
        
        var taskId = $(this).data('task-id');

        if (confirm("Are you sure you want to delete this task?")) {
            $.ajax({
                url: updateTaskURL, 
                method: "POST",
                headers: { "X-CSRFToken": getCSRFToken() },
                data: {
                    task_id: taskId,
                    delete: true
                },
                success: function(response) {
                    if (response.status === 'success') {
                        console.log("Task deleted successfully", response);
                        $(`#task-${taskId}`).remove();
                    } else {
                        alert(response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error deleting task', xhr.responseText);
                }
            });
        }
    });
    $(".editable-task").on('blur', function() {
        if ($(this).hasClass('deleting')) { 
            return;
        }
        var taskId = $(this).data('task-id');
        var taskText = $(this).data('task_text');
        var newTaskText = $(`.editable-task[data-task-id="${taskId}"]`).text().trim();

        if (newTaskText.length === 0) {
            alert("Task cannot be empty!");
            return;
        }
        if (newTaskText.length > 255) {
            alert("Task is too long!");
            return;
        }
        if (!/[a-zA-Z0-9]/.test(newTaskText)) { 
            alert("Task must contain at least one letter or number.");
            return;
        }

        if (newTaskText !== null && newTaskText !== taskText) {
            $.ajax({
                url: updateTaskURL,
                method: "POST",
                headers: { "X-CSRFToken": getCSRFToken() },
                data: {
                    task_id: taskId,
                    task_text: newTaskText
                },
                success: function(response) {
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    } else {
                        console.log("Task updated successfully", response);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error updating task', xhr.responseText);
                }
            });
        }
    });
});