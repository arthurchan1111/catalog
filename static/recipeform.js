function addItem(){
  var element= document.createElement('Input');
  element.type= 'Number';
  element.placeholder= "Quantity";
  element.name ="two";
  var foo = document.getElementById('group');
    foo.appendChild(element);
}
