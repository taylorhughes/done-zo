var Signup={CHECK_DELAY:500,onKeyDown:function(A){if(Signup.checking){clearTimeout(Signup.checking)}Signup.checking=setTimeout(Signup.check,Signup.CHECK_DELAY)},check:function(A){var B=$F(Signup.nameField);if(!Signup.lastChecked||Signup.lastChecked!=B){Signup.lastChecked=B;new Ajax.Request(Signup.availabilityURL,{method:"get",parameters:{name:B},onSuccess:Signup.doCheck})}},doCheck:function(G){var F=Signup.elementFromText(G,"a");var E=$("availability");var B=E.parentNode;B.insertBefore(F,E);B.removeChild(E);var A=Signup.elementFromText(G,"p");var D=$("unavailable_message");var C=$("buttons");B=C.parentNode;if(D){B.removeChild(D)}B.insertBefore(A,C)},elementFromText:function(D,A){var B=new Element("div");B.innerHTML=D.responseText;var C=B.select(A);if(C.length>0){return C[0]}return null},load:function(A){Signup.nameField=$("name");Signup.availabilityURL=$("availability").href;Signup.nameField.observe("keydown",Signup.onKeyDown)}};Event.observe(window,"load",Signup.load);