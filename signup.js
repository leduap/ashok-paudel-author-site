// Newsletter sign-up. Loaded only on pages that have the sign-up box.
// Sends the address to the newsletter provider in the background and shows the thank-you
// line in place of the form. If the provider does not answer in the expected way, the form
// is sent the ordinary way and the provider shows its own confirmation page instead.

(function () {
  "use strict";

  document.querySelectorAll("form.signup-form").forEach(function (form) {
    var status = form.parentNode.querySelector(".signup-status");
    var button = form.querySelector("button");

    form.addEventListener("submit", function (event) {
      if (!window.fetch || !window.FormData || !status) { return; }
      event.preventDefault();
      button.disabled = true;

      fetch(form.action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
        .then(function (response) { return response.json(); })
        .then(function (result) {
          if (result && result.status === "success") {
            form.hidden = true;
            status.textContent = form.getAttribute("data-thanks") || "Thank you.";
            status.hidden = false;
          } else if (result && result.status === "quarantined" && /^https:\/\//.test(result.url || "")) {
            // The provider wants the visitor to pass a quick "are you human" check first.
            window.location.href = result.url;
          } else {
            form.submit();
          }
        })
        .catch(function () { form.submit(); });
    });
  });
})();
