// Elements
const recovryDashboardElement = document.getElementById("recovery-dashboard");
const navigationIconContainerElement = document.getElementById("navigation-icon-elements");


// event handlers



// messages elements
const messageContainerElement = document.getElementById("messages");
const messagePTag = document.getElementById("message-p-tag");


// navigation icon
const hamburgerOpenIcon = document.getElementById("open-hamburger-nav-icon");
const closeXIcon = document.getElementById("close-nav-icon");



// constants
const OPEN_NAV_BAR_HAMBURGERR_ICON = "open-hamburger-nav-icon";
const CLOSE_NAV_BAR_ICON = "close-nav-icon";



export function toggleSideBarIcon(navIconElement) {

    if (navIconElement.id !== OPEN_NAV_BAR_HAMBURGERR_ICON && navIconElement.id !== CLOSE_NAV_BAR_ICON) {
        return;
    }

    let isNavOpen = true;

    if (navIconElement.id === OPEN_NAV_BAR_HAMBURGERR_ICON) {
        navIconElement.classList.add("rotate-360")
    }

    if (navIconElement.id === CLOSE_NAV_BAR_ICON) {
        isNavOpen = false;
        navIconElement.classList.add("rotate-360");
    }

    setTimeout(() => {

        if (isNavOpen) {
            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "block";

            navigationIconContainerElement.style.height = "auto";
            recovryDashboardElement.style.marginTop = "400px";

            navigationIconContainerElement.classList.add("active")

        } else {

            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "none";
            hamburgerOpenIcon.style.display = "block";
            navigationIconContainerElement.style.height = "0";
            recovryDashboardElement.style.marginTop = "65px";
            navigationIconContainerElement.classList.remove("active")


        }


    }, 500);
}
