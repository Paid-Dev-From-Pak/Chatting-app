let socket = io();
let to = localStorage.getItem("selectedUser") || "";

// register
socket.emit("register_user", user);

// LOAD CONTACTS
async function load(){
    let res = await fetch("/get_contacts");
    let data = await res.json();

    let div = document.getElementById("users");
    div.innerHTML="";

    data.forEach(u=>{
        let d=document.createElement("div");
        d.className="user";
        d.innerText=u;

        if(u===to) d.classList.add("active"); // highlight

        d.onclick=()=>{
            to=u;
            localStorage.setItem("selectedUser", to);
            load(); // refresh highlight
            loadMessages();
        };

        div.appendChild(d);
    });

    if(to){
    document.getElementById("chatHeader").innerText = to;
    loadMessages();
} else {
    document.getElementById("chatHeader").innerText = "No chat selected";
}
}
load();

// 🔥 LOAD HISTORY
async function loadMessages(){
    let res = await fetch("/get_messages/"+to);
    let msgs = await res.json();

    let box=document.getElementById("chatBox");
    box.innerHTML="";

    msgs.forEach(m=>{
        let d=document.createElement("div");
        d.className = m.from===user ? "me":"other";
        d.innerText = m.message;
        box.appendChild(d);
    });
}

// ADD CONTACT
async function addContact(){
    let name=prompt("Username?");
    if(!name)return;

    await fetch("/add_contact",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name})
    });

    load();
}

// REMOVE
async function removeContact(){
    if(!to)return;

    await fetch("/remove_contact",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:to})
    });

    localStorage.removeItem("selectedUser");
    to="";
    document.getElementById("chatBox").innerHTML="";
    load();
}

// SEND
function send(){
    let msg=document.getElementById("msg").value;
    if(!msg || !to) return alert("Select user");

    socket.emit("msg",{from:user,to:to,message:msg});
    document.getElementById("msg").value="";
}

// RECEIVE
socket.on("msg",m=>{
    if(m.from!==to && m.to!==to && m.from!==user) return;

    let d=document.createElement("div");
    d.className=m.from===user?"me":"other";
    d.innerText=m.message;

    document.getElementById("chatBox").appendChild(d);
});

// TYPING
document.getElementById("msg").addEventListener("input",()=>{
    if(!to)return;
    socket.emit("typing",{from:user,to:to});
});

socket.on("typing",d=>{
    if(d.from!==to)return;

    document.getElementById("typing").innerText=d.from+" typing...";
    setTimeout(()=>document.getElementById("typing").innerText="",1000);
});