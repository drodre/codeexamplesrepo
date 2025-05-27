<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('helloworld'); // Changed 'welcome' to 'helloworld'
});
