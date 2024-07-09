// document.addEventListener('DOMContentLoaded', () => {
//     console.log('Script main.js est chargé');

//     loadContent(window.location.pathname);

//     document.addEventListener('click', event => {
//         const link = event.target.closest('a');
//         if (link && isInternalLink(link)) {
//             event.preventDefault();
//             const path = new URL(link.href).pathname;
//             window.history.pushState({}, '', path);
//             loadContent(path);
//         }
//     });

//     document.addEventListener('submit', event => {
//         if (event.target.tagName === 'FORM') {
//             event.preventDefault();
//             submitForm(event.target);
//         }
//     });

//     window.addEventListener('popstate', () => {
//         loadContent(window.location.pathname);
//     });
// });

// function loadContent(path) {
//     console.log('Loading content from:', path);
//     fetch(path, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw new Error('Network response was not ok');
//         }
//         return response.json();
//     })
//     .then(data => {
//         if (data.redirect) {
//             window.location.href = data.redirect;
//         } else if (data.html) {
//             document.getElementById('app').innerHTML = data.html;
//             attachFormListeners();
//             attachLinkListeners();
//         }
//     })
//     .catch(error => console.error('Error loading content:', error));
// }

// function attachFormListeners() {
//     document.querySelectorAll('form').forEach(form => {
//         form.removeEventListener('submit', handleFormSubmit);
//         form.addEventListener('submit', handleFormSubmit);
//     });
// }

// function attachLinkListeners() {
//     document.querySelectorAll('a').forEach(link => {
//         if (isInternalLink(link)) {
//             link.removeEventListener('click', handleLinkClick);
//             link.addEventListener('click', handleLinkClick);
//         }
//     });
// }

// function handleFormSubmit(event) {
//     event.preventDefault();
//     submitForm(event.target);
// }

// function handleLinkClick(event) {
//     event.preventDefault();
//     const path = new URL(event.currentTarget.href).pathname;
//     window.history.pushState({}, '', path);
//     loadContent(path);
// }

// function submitForm(form) {
//     const formData = new FormData(form);
//     fetch(form.action, {
//         method: form.method || 'POST',
//         body: formData,
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw new Error('Network response was not ok');
//         }
//         return response.json();
//     })
//     .then(data => {
//         if (data.redirect) {
//             window.location.href = data.redirect;
//         } else if (data.html) {
//             document.getElementById('app').innerHTML = data.html;
//             attachFormListeners();
//             attachLinkListeners();
//         }
//     })
//     .catch(error => console.error('Error submitting form:', error));
// }

// function isInternalLink(link) {
//     return link.hostname === window.location.hostname;
// }


//2

// document.addEventListener('DOMContentLoaded', () => {
//     console.log('Script main.js est chargé');
	
// 	loadContent(window.location.pathname); //Charge le contenu de la page en fonction du chemin de l'URL actuelle (l'URL sans le domaine).

//     document.addEventListener('click', event => {
//         const link = event.target.closest('a');//Trouve le plus proche élément <a> par rapport à l'endroit où l'utilisateur a cliqué.
// 		console.log("Fonction principale : link =", link);
//         if (link) {
//             event.preventDefault();//Empêche le comportement par défaut du clic sur un lien, c'est-à-dire la navigation vers l'URL du lien
//             const path = new URL(link.href).pathname;// Extrait le chemin de l'URL du lien.
// 			console.log("Fonction principale : path =", path);
//             window.history.pushState({}, '', path);//Met à jour l'URL dans la barre d'adresse sans recharger la page.
//             loadContent(path);//Charge dynamiquement le contenu de la nouvelle URL en utilisant AJAX.
//         }
//     });

//     document.addEventListener('submit', event => {
//         if (event.target.tagName === 'FORM') {
//             event.preventDefault(); //Empêche la soumission normale du formulaire, pour gérer la soumission via AJAX.
//             submitForm(event.target);//Appelle la fonction submitForm pour soumettre le formulaire via AJAX.
//         }
//     });

//     window.addEventListener('popstate', () => { // Ajoute un gestionnaire d'événement pour les changements dans l'historique de navigation (comme le clic sur le bouton "Retour")
//         loadContent(window.location.pathname);
//     });
// });

// function loadContent(path) {
//     console.log('Loading content from:', path);
// 	fetch(path, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     }) //  Effectue une requête AJAX vers l'URL spécifiée avec un en-tête pour indiquer que la requête est une requête AJAX.
//     .then(response => {
// 		console.log("Je passe la")
//         if (!response.ok) {
//             throw new Error('Network response was not ok');
//         }
// 		console.log(response)
// 		console.log("reponse.json before =", response.json)
//         return response.json();
//     })
// 	console.log("reponse.json =", response.json)
//     .then(data => {
// 		console.log("Je passe ici")
// 		console.log(data)
//         if (data.redirect) {
//             window.location.href = data.redirect;
//         } else if (data.html) {
//             document.getElementById('app').innerHTML = data.html;
//             attachFormListeners();
//             attachLinkListeners();
//         }
//     })
//     .catch(error => console.error('Error loading content:', error));
// }


// function loadContent(path) {
//     console.log('Loading content from:', path);
//     fetch(path, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => response.text()) // Change to response.text() to debug
//     .then(text => {
//         console.log('Raw response:', text); // Log the raw response
//         try {
//             const data = JSON.parse(text); // Parse JSON manually
//             if (data.redirect) {
//                 window.location.href = data.redirect;
//             } else if (data.html) {
//                 document.getElementById('app').innerHTML = data.html;
//                 attachFormListeners();
//                 attachLinkListeners();
//             }
//         } catch (error) {
//             console.error('Error parsing JSON:', error);
//             document.getElementById('app').innerHTML = text; // Display the HTML in the app div for debugging
//         }
//     })
//     .catch(error => console.error('Error loading content:', error));
// }

// function attachFormListeners() {
//     document.querySelectorAll('form').forEach(form => {
//         form.addEventListener('submit', event => {
//             event.preventDefault();
//             submitForm(event.target);
//         });
//     });
// }

// function attachLinkListeners() {
//     document.querySelectorAll('a').forEach(link => {
//         link.addEventListener('click', event => {
//             event.preventDefault();
//             const path = new URL(link.href).pathname;
//             window.history.pushState({}, '', path);
//             loadContent(path);
//         });
//     });
// }

// function submitForm(form) {
//     const formData = new FormData(form);
//     fetch(form.action, {
//         method: form.method || 'POST',
//         body: formData,
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => response.text()) // Change to response.text() to debug
//     .then(text => {
//         console.log('Raw response:', text); // Log the raw response
//         try {
//             const data = JSON.parse(text); // Parse JSON manually
//             if (data.redirect) {
//                 window.location.href = data.redirect;
//             } else if (data.html) {
//                 document.getElementById('app').innerHTML = data.html;
//                 attachFormListeners();
//                 attachLinkListeners();
//             }
//         } catch (error) {
//             console.error('Error parsing JSON:', error);
//             document.getElementById('app').innerHTML = text; // Display the HTML in the app div for debugging
//         }
//     })
//     .catch(error => console.error('Error submitting form:', error));
// }





//3

// document.addEventListener('DOMContentLoaded', () => {
//     console.log('Script main.js est chargé');
    
//     loadContent(window.location.pathname);

//     document.addEventListener('click', event => {
//         const link = event.target.closest('a');
//         if (link) {
//             event.preventDefault();
//             const path = new URL(link.href).pathname;
//             window.history.pushState({}, '', path);
//             loadContent(path);
//         }
//     });

//     window.addEventListener('popstate', () => {
//         loadContent(window.location.pathname);
//     });
// });

// function loadContent(path) {
//     fetch(path, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => response.text())
//     .then(text => {
//         try {
//             const data = JSON.parse(text);
//             if (data.redirect) {
//                 window.location.href = data.redirect;
//             } else if (data.html) {
//                 document.getElementById('app').innerHTML = data.html;
//                 attachFormListeners();
//                 attachLinkListeners();
//             }
//         } catch (error) {
//             document.getElementById('app').innerHTML = text;
//         }
//     })
//     .catch(error => console.error('Error loading content:', error));
// }

// function attachFormListeners() {
//     document.querySelectorAll('form').forEach(form => {
//         form.addEventListener('submit', event => {
//             event.preventDefault();
//             submitForm(event.target);
//         });
//     });
// }

// function attachLinkListeners() {
//     document.querySelectorAll('a').forEach(link => {
//         link.addEventListener('click', event => {
//             event.preventDefault();
//             const path = new URL(link.href).pathname;
//             window.history.pushState({}, '', path);
//             loadContent(path);
//         });
//     });
// }

// function submitForm(form) {
//     const formData = new FormData(form);
//     fetch(form.action, {
//         method: form.method || 'POST',
//         body: formData,
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => response.text())
//     .then(text => {
//         try {
//             const data = JSON.parse(text);
//             if (data.redirect) {
//                 window.location.href = data.redirect;
//             } else if (data.html) {
//                 document.getElementById('app').innerHTML = data.html;
//                 attachFormListeners();
//                 attachLinkListeners();
//             }
//         } catch (error) {
//             document.getElementById('app').innerHTML = text;
//         }
//     })
//     .catch(error => console.error('Error submitting form:', error));
// }


//4






// Écouter l'événement popstate pour gérer les navigations arrière/avant







// IMRANE

document.addEventListener('DOMContentLoaded', () => {
    console.log('Script main.js est chargé');

//     window.addEventListener('popstate', event => {
//         // event.preventDefault();
//         console.log("On rentre ici");
//         printCustomHistory();
//         console.log("window.location.pathname = ", window.location.pathname)
//         loadContent(window.location.pathname);
//  });

    // window.addEventListener('popstate', event => {
    //     if (event.state && event.state.path) {
    //         console.log('On rentre ici avec', event.state.path);
    //         loadContent(event.state.path);
    //     } else {
    //         // Cas où il n'y a pas d'état, on peut utiliser la location actuelle
    //         console.log('On rentre ici avec', window.location.pathname);
    //         loadContent(window.location.pathname);
    //     }
    // });

    window.addEventListener('popstate', event => {
        console.log("event = ", event);
        if (event.state && event.state.path) {
            console.log('Navigating to:', event.state.path);
            const path = event.state.path;
            currentIndex = customHistory.indexOf(path); // Synchronize custom history index
            // let i = customHistory.length;
            // while (i > 0)
            // {
            //     if (customHistory[i] === event.state.path)
            //     {
            //         currentIndex = i;
            //         break;
            //     }
            //     i--;
            // }
            console.log("current index apres indexOf", currentIndex);
            loadContent(path, false); // Load content without adding to history
        } else {
            // Cas où il n'y a pas d'état, on peut utiliser la location actuelle
            console.log('Navigating to current path:', window.location.pathname);
            loadContent(window.location.pathname, false); // Load content without adding to history
        }
    });

    document.addEventListener('click', event => {
        const link = event.target.closest('a');
        console.log("Fonction principale : link =", link);
        if (link) {
            event.preventDefault();
            const path = new URL(link.href).pathname;
            console.log("Fonction principale : path =", path);
            //window.history.pushState({}, '', path);
            loadContent(path, true);
        }
    });
    

    // Gestionnaire d'événements pour les formulaires
    document.addEventListener('submit', event => {
        console.log("target = ", event.target.tagName);
        if (event.target.tagName === 'FORM') {
            event.preventDefault();
            submitForm(event.target);
        }
    });

    // Gestionnaire d'événements pour les changements dans l'historique de navigation
    
    
     
    

    // Gestionnaire d'événements pour le bouton de déconnexion
    /*
    const logoutButton = document.querySelector('#logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', event => {
            event.preventDefault();
            fetch('/logout/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            //.then(data => {
            //    if (data.redirect) {
            //        window.location.href = data.redirect;
            //    }
            //})
            .catch(error => console.error('Error during logout:', error));
        });
    }
        */
});



// DEFINITIONB DES FONCTIONS

let customHistory = [];
let currentIndex = -1;


function loadContent(path, addToHistory) {
    console.log("addTohistory = ", addToHistory);
    console.log('Loading content from:', path);
    let toggle = false;
    fetch(path, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.text())
    .then(text => {
        console.log('Raw response:', text);
        try {
            const data = JSON.parse(text);
            console.log("data =", data);
            
            if (data.html) {
                document.getElementById('app').innerHTML = data.html;
                if (addToHistory) {
                    if (currentIndex === customHistory.length - 1)
                    {
                        if (customHistory[currentIndex] != data.url)
                        {
                            customHistory.push(data.url);
                            currentIndex++;
                            toggle = true;
                        }
                    }
                    else
                    {
                        customHistory = customHistory.slice(0, currentIndex + 1);
                        console.log("Custom history quand on tronque l'historique", customHistory)
                        customHistory.push(data.url);
                        currentIndex = customHistory.length - 1;
                    }
                    if (toggle === true)
                        window.history.pushState({ path: data.url }, '', data.url);
                }
                console.log("customHistory =", customHistory);
                console.log("currentIndex =", currentIndex);
            } else {
                console.error('data.html is undefined');
                document.getElementById('app').innerHTML = text;
            }
        } catch (error) {
            console.error('Error parsing JSON:', error);
            document.getElementById('app').innerHTML = text;
        }
    })
    .catch(error => console.error('Error loading content:', error));
}


// let customHistory = [];

// function loadContent(path) {
//     console.log('Loading content from:', path);
//     fetch(path, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//     })
//     .then(response => response.text()) // Change to response.text() to debug
//     .then(text => {
//         console.log('Raw response:', text); // Log the raw response
//         try {
//             const data = JSON.parse(text); // Parse JSON manually
//             console.log("data =", data);
//             if (data.url)
//             {
//                 console.log("data url =", data.url);
//                 console.log("Chargement URL ok")
//                 customHistory.push(data.url);
//                 printCustomHistory();
//                 window.history.pushState({path : data.url}, '', data.url);
//             }
//             else
//             {
//                 console.log("Url not catched or defined");
//             }
//             if (data.html)
//                 document.getElementById('app').innerHTML = data.html;
//             else
//                 console.log("error loading html");
//             //attachFormListeners();
//             //attachLinkListeners();
//         } catch (error) {
//             console.error('Error parsing JSON:', error);
//             document.getElementById('app').innerHTML = text; // Display the HTML in the app div for debugging
//         }
//     })
//     .catch(error => console.error('Error loading content:', error));
// }




function printCustomHistory()
{
    console.log("Custom History =", customHistory);
}

/*
function attachFormListeners() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            submitForm(event.target);
        });
    });
}

function attachLinkListeners() {
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            const path = new URL(link.href).pathname;
            //window.history.pushState({}, '', path);
            loadContent(path);
        });
    });
}
*/
function submitForm(form) {
    const formData = new FormData(form);
    console.log("Submitting form:", form.action);
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.text()) // Change to response.text() to debug
    .then(text => {
        console.log('Raw response:', text); // Log the raw response
        try {
            const data = JSON.parse(text); // Parse JSON manually
            console.log("Parsed response:", data);
            window.history.pushState({}, '', data.url);
            document.getElementById('app').innerHTML = data.html;
            //attachFormListeners();
            //attachLinkListeners();
        } catch (error) {
            console.error('Error parsing JSON:', error);
            document.getElementById('app').innerHTML = text; // Display the HTML in the app div for debugging
        }
    })
    .catch(error => console.error('Error submitting form:', error));
}






/*
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;

}
*/  

