function deleteNote(noteId) {
  if (confirm('Are you sure you want to delete this note? This action is permanent.')) {
    fetch("/delete-note", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ noteId: noteId }),
    }).then((response) => {
      if (response.ok) {
        window.location.href = "/";
      } else {
        alert('Error deleting note.');
      }
    }).catch(error => {
      console.error('Error:', error);
      alert('An error occurred.');
    });
  }
}

function editNote(noteId) {
  const newContent = prompt('Editează notița:', '');
  if (newContent !== null && newContent.trim() !== '') {
    fetch("/edit-note", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        noteId: noteId,
        newData: newContent.trim()
      }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        window.location.href = "/";
      } else {
        alert('Eroare: ' + data.error);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('A apărut o eroare.');
    });
  }
}