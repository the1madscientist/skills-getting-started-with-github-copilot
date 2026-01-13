document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Fetch and display activities from the API
  async function loadActivities() {
    try {
      const response = await fetch("/activities");
      const activitiesData = await response.json();

      // Convert object to array format
      const activitiesArray = Object.keys(activitiesData).map((name) => ({
        name,
        ...activitiesData[name],
      }));

      displayActivities(activitiesArray);
      populateActivityDropdown(activitiesArray);
    } catch (error) {
      console.error("Error loading activities:", error);
      document.getElementById(
        "activities-list"
      ).innerHTML = `<p>Error loading activities. Please try again later.</p>`;
    }
  }

  function displayActivities(activities) {
    activitiesList.innerHTML = "";

    activities.forEach((activity) => {
      const { name, description, schedule, participants, max_participants } =
        activity;

      const activityCard = document.createElement("div");
      activityCard.classList.add("activity-card");

      activityCard.innerHTML = `
        <h4>${name}</h4>
        <p>${description}</p>
        <p class="schedule"><strong>Schedule:</strong> ${schedule}</p>
        <p class="capacity"><strong>Capacity:</strong> ${participants.length}/${max_participants}</p>
        <div class="participants-section">
            <strong>Participants:</strong>
            <ul class="participants-list">
                ${
                  participants.length > 0
                    ? participants.map((email) => `
                        <li>
                            <span class="participant-email">${email}</span>
                            <button class="delete-btn" data-activity="${name}" data-email="${email}" title="Remove participant">🗑️</button>
                        </li>
                    `).join("")
                    : '<li class="no-participants">No participants yet</li>'
                }
            </ul>
        </div>
      `;

      activitiesList.appendChild(activityCard);
    });

    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', handleDeleteParticipant);
    });
  }

  async function handleDeleteParticipant(event) {
    const button = event.target;
    const activityName = button.getAttribute('data-activity');
    const email = button.getAttribute('data-email');

    if (!confirm(`Are you sure you want to remove ${email} from ${activityName}?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activityName)}/participant?email=${encodeURIComponent(email)}`,
        {
          method: 'DELETE',
        }
      );

      const data = await response.json();

      if (response.ok) {
        showMessage(`Successfully removed ${email} from ${activityName}`, 'success');
        // Reload activities to show updated participants
        await loadActivities();
      } else {
        showMessage(data.detail || 'Error removing participant', 'error');
      }
    } catch (error) {
      console.error('Error removing participant:', error);
      showMessage('Error removing participant. Please try again.', 'error');
    }
  }

  function populateActivityDropdown(activities) {
    // Keep the default option
    activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

    activities.forEach((activity) => {
      const option = document.createElement("option");
      option.value = activity.name;
      option.textContent = activity.name;
      activitySelect.appendChild(option);
    });
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activityName = document.getElementById("activity").value;

    if (!email || !activityName) {
      showMessage("Please fill in all fields", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(
          email
        )}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (response.ok) {
        showMessage(`Successfully signed up for ${activityName}!`, "success");
        // Reset form
        signupForm.reset();
        // Reload activities to show updated participants
        await loadActivities();
      } else {
        showMessage(data.detail || "Error signing up", "error");
      }
    } catch (error) {
      console.error("Error signing up:", error);
      showMessage("Error signing up. Please try again.", "error");
    }
  });

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Load activities when page loads
  loadActivities();
});
