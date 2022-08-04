const sideMenu = document.querySelector("aside");
const menuBtn = document.querySelector("#menu-btn");
const closeBtn = document.querySelector("#close-btn");
const themeToggler = document.querySelector(".theme-toggler");

menuBtn.addEventListener('click',()=>{
    sideMenu.style.display = 'block';
})

closeBtn.addEventListener('click',()=>{
    sideMenu.style.display = 'none';
})


themeToggler.addEventListener('click',()=>{
    document.body.classList.toggle('dark-theme-variables');
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active');
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active');
})

//PRELOADER
var loader = document.querySelector('.prev-center');
window.addEventListener("load",function(){
    loader.style.display = "none";
});

//SHOW MODAL
function showModal(classattr) {
    var body = document.querySelector('.container');
    body.classList.toggle('active-modal');

    var modal = document.querySelector('.'+classattr);
    modal.classList.toggle('active-md');
}

//TAB NAVIGATION
let tabs = document.querySelectorAll('.tabs__toggle'),
    contents = document.querySelectorAll('.tabs__content');

    tabs.forEach((tab,index) => {
        tab.addEventListener('click', ()=>{
            contents.forEach((content)=>{
                content.classList.remove('active');
            });

            tabs.forEach((tab)=>{
                tab.classList.remove('active');
            });

            contents[index].classList.add('active');
            tabs[index].classList.add('active');
        });
    });

