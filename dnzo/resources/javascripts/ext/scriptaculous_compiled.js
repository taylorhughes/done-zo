var Scriptaculous={Version:"1.8.2",REQUIRED_PROTOTYPE:"1.6.0.3",load:function(){function A(B){var C=B.replace(/_.*|\./g,"");C=parseInt(C+"0".times(4-C.length));return B.indexOf("_")>-1?C-1:C}if((typeof Prototype=="undefined")||(typeof Element=="undefined")||(typeof Element.Methods=="undefined")||(A(Prototype.Version)<A(Scriptaculous.REQUIRED_PROTOTYPE))){throw ("script.aculo.us requires the Prototype JavaScript framework >= "+Scriptaculous.REQUIRED_PROTOTYPE)}}};Scriptaculous.load();