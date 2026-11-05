document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.bd-sidenav a[href$="output-overview.html"]').forEach((link) => {
    const dropdown = link.parentElement.querySelector(":scope > details");
    if (dropdown) dropdown.open = true;
  });
});
