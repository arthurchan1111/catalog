app.controller("recipectrl", function($scope, $http){
$scope.ingredient ={};
$scope.ingredients = [1];
$scope.addItem = function(){
var name= $scope.ingredient.name;
var measurement = $scope.ingredient.measurement;
var quantity = $scope.ingredient.quantity;
 //$scope.ingredient ={};
 $scope.ingredients.push({"quantity" : quantity, "measurement" : measurement, "name": name});

 console.log($scope.ingredients);
};

$scope.removeItem = function (x) {
      $scope.ingredients.splice(x, 1);
  }

$scope.senddata = function(){
  $http.post('/create', $scope.ingredients, {headers: {'Content-Type': 'application/json'}})
             .success(function(){alert('ok')})
             .error(function(){alert('fail')});

}


});
