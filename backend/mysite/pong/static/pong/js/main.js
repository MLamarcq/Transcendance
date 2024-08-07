
var displayChatInterval = null;
var checkGameStatusInterval;
var searchingMatchInterval;

var customHistory = [new URL(window.location.href).pathname];
var currentIndex = 0;
var csrftoken = getCookie('csrftoken');
console.log(csrftoken)

function is_there_a_tournament(data) {
	var tournament = document.getElementById('tournament')
	if (data.status
	&& window.location.href.indexOf('waiting') == -1
	&& window.location.href.indexOf('pong') == -1
	&& window.location.href.indexOf('tic/') == -1
	&& window.location.href.indexOf('tournament') == -1)
	{
		tournament.style.display = "flex";
		setTimeout(() =>{
			tournament.style.opacity = ".65";
		}, 300)
		tournament.innerHTML = "A tournament is waiting for participant";
	}
	else
	{
		tournament.style.opacity = "0";
		setTimeout(() =>{
			tournament.style.display = "none";
		}, 400)
	}
}

document.addEventListener('DOMContentLoaded', () => {

	console.log('Script main.js est chargé');

	var invit = document.getElementById('invit')
	var opponent = document.getElementById('opponent')
	var is_invited = false;
	var csrftoken = getCookie('csrftoken');

	var InvitationInterval = setInterval(() => {
		$.ajax({
			url: '/looking_for_invitation/',
			type: 'POST',
			async: false,
			beforeSend: function(xhr) {
				xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			},
			success: function(data_invit)
			{
				console.log(data_invit);
				if (data_invit.status && is_invited == false)
				{
					invit.style.display = "block";
					setTimeout(() =>{
						invit.style.opacity = "1";
					}, 300)
					opponent.innerHTML = data_invit.opponent;

					is_invited = true;
					function accept() {
						is_invited = false
						document.querySelector('#invit #accept').removeEventListener('click', accept)
						document.querySelector('#invit #refuse').removeEventListener('click', refuse)
						invit.style.opacity = "0";
						setTimeout(() =>{
							invit.style.display = "none";
						}, 400)
						$.ajax({
							url: '/invitation_response/',
							type: 'POST',
							data: {
								'accept': "1",
								'opponent': data_invit.opponent
							},
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function(created_party){
								var toggle = false;
								fetch(created_party.url, {
									headers: { 'X-Requested-With': 'XMLHttpRequest' }
								})
								.then(response => response.text())
								.then(text => {
									try {
										const data = JSON.parse(text);
										if (data.html) {
											document.getElementById('app').innerHTML = data.html;
											script_array = Array.from(document.getElementById('app').querySelectorAll("script"));
											script_array.forEach((script) => {
												var new_script = document.createElement('script');
												new_script.innerHTML = script.textContent;
												script.remove();
												document.getElementById('app').appendChild(new_script);
											})
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
											console.log("custom_hisotry = ", data)
											if (customHistory.length > 2
											&& customHistory[customHistory.length - 1].indexOf('pong_page') == -1
											&& customHistory[customHistory.length - 2].indexOf('waiting_pong') != -1)
											{
												$.ajax({
													url: '/stop_waiting_pong/',
													type: 'POST',
													async: false,
													beforeSend: function(xhr) {
														xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
													},
													success: function() {}
												});
											}
											if (customHistory.length > 2
											&& customHistory[customHistory.length - 1].indexOf('tic') == -1
											&& customHistory[customHistory.length - 2].indexOf('waiting_tic') != -1)
											{
												$.ajax({
													url: '/stop_waiting_tic/',
													type: 'POST',
													async: false,
													beforeSend: function(xhr) {
														xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
													},
													success: function() {}
												});
											}
										}
										else
										{
											console.error('data.html is undefined');
											document.getElementById('app').innerHTML = text;
										}
									} catch (error) {
										console.error('Error parsing JSON:', error);
										document.getElementById('app').innerHTML = text;
									}
								})
							}
						})
					}
					function refuse() {
						is_invited = false
						document.querySelector('#invit #accept').removeEventListener('click', accept)
						document.querySelector('#invit #refuse').removeEventListener('click', refuse)
						invit.style.opacity = "0";
						setTimeout(() =>{
							invit.style.display = "none";
						}, 400)
						$.ajax({
							url: '/invitation_response/',
							type: 'POST',
							data: {
								'accept': "0",
								'opponent': data_invit.opponent
							},
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function(){}
						})
					}

					document.querySelector('#invit #accept').addEventListener('click', accept)
					document.querySelector('#invit #refuse').addEventListener('click', refuse)

				}
			}
		});
		$.ajax({
			url: '/looking_for_tournament/',
			type: 'POST',
			async: false,
			beforeSend: function(xhr) {
				xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			},
			success: function(data_tournament)
			{
				is_there_a_tournament(data_tournament);
			}
		});

	}, 2000)

	window.addEventListener('popstate', event => {
		if (event.state && event.state.path) {
			const path = event.state.path;
			currentIndex = customHistory.indexOf(path); // Synchronize custom history index
			// var i = customHistory.length;
			// while (i > 0)
			// {
			//     if (customHistory[i] === event.state.path)
			//     {
			//         currentIndex = i;
			//         break;
			//     }
			//     i--;
			// }
			loadContent(path, false); // Load content without adding to history
		} else {
			// Cas où il n'y a pas d'état, on peut utiliser la location actuelle
			loadContent(window.location.pathname, false); // Load content without adding to history
		}
	});

	document.addEventListener('click', event => {
		const link = event.target.closest('a');
		if (link) {
			event.preventDefault();
			const path = new URL(link.href).pathname;
			//window.history.pushState({}, '', path);
			loadContent(path, true);
		}
	});

	// Gestionnaire d'événements pour les formulaires
	document.addEventListener('submit', event => {
		if (event.target.tagName === 'FORM') {
			event.preventDefault();
			submitForm(event.target, true);
		}
	});
});



// DEFINITIONB DES FONCTIONS


function send_score_quit(id_party) {
	if (id_party)
	{
		$.ajax({
			url: '/scoring_pong/' + id_party + '/',
			type: 'POST',
			async: false,
			beforeSend: function(xhr) {
				xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			},
			data: {
				'red_score': 0,
				'blue_score': 0,
				'exchanges': 0,
				'game_time': 0,
			},
			success: function() {
				// would you like to restart ?
			}
		});
	}
}

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}


function loadContent(path, addToHistory) {

	var csrftoken = getCookie('csrftoken');
	var i_clear_interval = -1;
	while (++i_clear_interval < 2000)
		clearInterval(i_clear_interval);
	var invit = document.getElementById('invit')
	var opponent = document.getElementById('opponent')
	var is_invited = false;

	var InvitationInterval = setInterval(() => {
		$.ajax({
			url: '/looking_for_invitation/',
			type: 'POST',
			async: false,
			beforeSend: function(xhr) {
				xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			},
			success: function(data_invit)
			{
				if (data_invit.status && is_invited == false)
				{
					invit.style.display = "block";
					setTimeout(() =>{
						invit.style.opacity = "1";
					}, 300)
					opponent.innerHTML = data_invit.opponent;

					is_invited = true;
					function accept() {
						is_invited = false
						document.querySelector('#invit #accept').removeEventListener('click', accept)
						document.querySelector('#invit #refuse').removeEventListener('click', refuse)
						invit.style.opacity = "0";
						setTimeout(() =>{
							invit.style.display = "none";
						}, 400)
						$.ajax({
							url: '/invitation_response/',
							type: 'POST',
							data: {
								'accept': "1",
								'opponent': data_invit.opponent
							},
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function(created_party){
								var toggle = false;
								fetch(created_party.url, {
									headers: { 'X-Requested-With': 'XMLHttpRequest' }
								})
								.then(response => response.text())
								.then(text => {
									try {
										const data = JSON.parse(text);
										if (data.html) {
											document.getElementById('app').innerHTML = data.html;
											script_array = Array.from(document.getElementById('app').querySelectorAll("script"));
											script_array.forEach((script) => {
												var new_script = document.createElement('script');
												new_script.innerHTML = script.textContent;
												script.remove();
												document.getElementById('app').appendChild(new_script);
											})
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
												customHistory.push(data.url);
												currentIndex = customHistory.length - 1;
											}
											if (toggle === true)
												window.history.pushState({ path: data.url }, '', data.url);
											if (customHistory.length > 2
											&& customHistory[customHistory.length - 1].indexOf('pong_page') == -1
											&& customHistory[customHistory.length - 2].indexOf('waiting_pong') != -1)
											{
												$.ajax({
													url: '/stop_waiting_pong/',
													type: 'POST',
													async: false,
													beforeSend: function(xhr) {
														xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
													},
													success: function() {}
												});
											}
											if (customHistory.length > 2
											&& customHistory[customHistory.length - 1].indexOf('tic') == -1
											&& customHistory[customHistory.length - 2].indexOf('waiting_tic') != -1)
											{
												$.ajax({
													url: '/stop_waiting_tic/',
													type: 'POST',
													async: false,
													beforeSend: function(xhr) {
														xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
													},
													success: function() {}
												});
											}
										}
										else
										{
											console.error('data.html is undefined');
											document.getElementById('app').innerHTML = text;
										}
									} catch (error) {
										console.error('Error parsing JSON:', error);
										document.getElementById('app').innerHTML = text;
									}
								})
							}
						})
					}
					function refuse() {
						is_invited = false
						document.querySelector('#invit #accept').removeEventListener('click', accept)
						document.querySelector('#invit #refuse').removeEventListener('click', refuse)
						invit.style.opacity = "0";
						setTimeout(() =>{
							invit.style.display = "none";
						}, 400)
						$.ajax({
							url: '/invitation_response/',
							type: 'POST',
							data: {
								'accept': "0",
								'opponent': data_invit.opponent
							},
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function(){}
						})
					}

					document.querySelector('#invit #accept').addEventListener('click', accept)
					document.querySelector('#invit #refuse').addEventListener('click', refuse)

				}
			}
		});
		$.ajax({
			url: '/looking_for_tournament/',
			type: 'POST',
			async: false,
			beforeSend: function(xhr) {
				xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			},
			success: function(data_tournament)
			{
				is_there_a_tournament(data_tournament);
			}
		});
	}, 2000)
	if (customHistory.length > 1
	&& customHistory[customHistory.length - 1].indexOf('pong_page') != -1)
	{
		var id_party = customHistory[customHistory.length - 1].match(/\/pong_page\/(\d+)\//)
		if (id_party)
			id_party = id_party[1];
		send_score_quit(id_party);
	}
	if (customHistory.length > 1
	&& customHistory[customHistory.length - 1].indexOf('tic') != -1)
	{
		var id_party = customHistory[customHistory.length - 1].match(/\/tic\/(\d+)\//)
		if (id_party)
			id_party = id_party[1];
		send_score_quit(id_party);
	}
	var toggle = false;
	fetch(path, {
		headers: { 'X-Requested-With': 'XMLHttpRequest' }
	})
	.then(response => response.text())
	.then(text => {
		try {
			const data = JSON.parse(text);
			if (data.html) {
				document.getElementById('app').innerHTML = data.html;
				script_array = Array.from(document.getElementById('app').querySelectorAll("script"));
				script_array.forEach((script) => {
					var new_script = document.createElement('script');
					new_script.innerHTML = script.textContent;
					script.remove();
					document.getElementById('app').appendChild(new_script);
				})
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
						customHistory.push(data.url);
						currentIndex = customHistory.length - 1;
					}
					if (toggle === true)
						window.history.pushState({ path: data.url }, '', data.url);
				}
				if (customHistory.length > 2
					&& customHistory[customHistory.length - 1].indexOf('pong_page') == -1
					&& customHistory[customHistory.length - 2].indexOf('waiting_pong') != -1)
					{
						$.ajax({
							url: '/stop_waiting_pong/',
							type: 'POST',
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function() {}
						});
					}
					if (customHistory.length > 2
					&& customHistory[customHistory.length - 1].indexOf('tic') == -1
					&& customHistory[customHistory.length - 2].indexOf('waiting_tic') != -1)
					{
						$.ajax({
							url: '/stop_waiting_tic/',
							type: 'POST',
							async: false,
							beforeSend: function(xhr) {
								xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
							},
							success: function() {}
						});
					}
			}
			else
			{
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




function submitForm(form, addToHistory) {
	var csrftoken = getCookie('csrftoken');
	const formData = new FormData(form);
	var toggle = false;
	fetch(form.action, {
		method: form.method || 'POST',
		body: formData,
		headers: { 'X-Requested-With': 'XMLHttpRequest' }
	})
	.then(response => response.text()) // Change to response.text() to debug
	.then(text => {
		try {
			const data = JSON.parse(text); // Parse JSON manually
			if (data.html)
				document.getElementById('app').innerHTML = data.html;
				script_array = Array.from(document.getElementById('app').querySelectorAll("script"));
				script_array.forEach((script) => {
					var new_script = document.createElement('script');
					new_script.innerHTML = script.textContent;
					script.remove();
					document.getElementById('app').appendChild(new_script);
				})
				// script_array = Array.from(document.getElementById('app').querySelectorAll("script"));
				// script_array.forEach((script) => {
				//     var new_script = document.createElement('script');
				//     new_script.innerHTML = script.textContent;
				//     script.remove();
				//     document.body.appendChild(new_script);
				// })
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
			else
			{
				console.error('data.html is undefined');
				document.getElementById('app').innerHTML = text;
			}
		} catch (error) {
			console.error('Error parsing JSON:', error);
			document.getElementById('app').innerHTML = text; // Display the HTML in the app div for debugging
		}
	})
	.catch(error => console.error('Error submitting form:', error));
}
