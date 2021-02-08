'use strict';
var avoidance_toggleBtn = document.getElementById('avoidance_toggle'); 
var cruise_toggleBtn = document.getElementById('cruise_toggle'); 
var upBtn = document.getElementById('up'); 
var downBtn = document.getElementById('down'); 
var leftBtn = document.getElementById('left'); 
var rightBtn = document.getElementById('right'); 
var stopBtn = document.getElementById('stop'); 
var t_avoidance_toggle = false;
var t_cruise_toggle = false;

avoidance_toggleBtn.addEventListener('click', avoidance_toggleRecord);
cruise_toggleBtn.addEventListener('click', cruise_toggleRecord);
upBtn.addEventListener('click', upRecord);
downBtn.addEventListener('click', downRecord);
leftBtn.addEventListener('click', leftRecord);
rightBtn.addEventListener('click', rightRecord);
stopBtn.addEventListener('click', stopRecord);

function avoidance_toggleRecord(){
    t_avoidance_toggle = !t_avoidance_toggle;
    if (t_avoidance_toggle == true){
        $.ajax({
            type: "POST", 
            url:'/webRTC/avoidance/',
            data: {'avoidance_status': 1}      
        }).done(function(msg){ 
            console.log('check'); 
        });
    }else{
        $.ajax({
            type: "POST", 
            url:'/webRTC/avoidance/',
            data: {'avoidance_status': 0}      
        }).done(function(msg){ 
            console.log('check'); 
        });
    } 
}

function cruise_toggleRecord(){
    t_cruise_toggle = !t_cruise_toggle;
    if (t_cruise_toggle == true){
        $.ajax({
            type: "POST", 
            url:'/webRTC/cruise/',
            data: {'cruise_status': 1}      
        }).done(function(msg){ 
            console.log('check'); 
        });
    }else{
        $.ajax({
            type: "POST", 
            url:'/webRTC/cruise/',
            data: {'cruise_status': 0}      
        }).done(function(msg){ 
            console.log('check'); 
        });
    } 
}

function upRecord(){
    $.ajax({
        type: "POST", 
        url:'/webRTC/move_arrow/',
        data: {'move_arrow': "up"}      
    }).done(function(msg){ 
        console.log('check'); 
    });
}

function downRecord(){
    $.ajax({
        type: "POST", 
        url:'/webRTC/move_arrow/',
        data: {'move_arrow': "down"}      
    }).done(function(msg){ 
        console.log('check'); 
    });
}

function leftRecord(){
    $.ajax({
        type: "POST", 
        url:'/webRTC/move_arrow/',
        data: {'move_arrow': "left"}      
    }).done(function(msg){ 
        console.log('check'); 
    });
}

function rightRecord(){
    $.ajax({
        type: "POST", 
        url:'/webRTC/move_arrow/',
        data: {'move_arrow': "right"}      
    }).done(function(msg){ 
        console.log('check'); 
    });
}

function stopRecord(){
    $.ajax({
        type: "POST", 
        url:'/webRTC/move_arrow/',
        data: {'move_arrow': "stop"}      
    }).done(function(msg){ 
        console.log('check'); 
    });
}