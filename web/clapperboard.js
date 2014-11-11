angular.module('Clapperboard', [])
    .constant('ENDPOINT_URI', 'http://minuteware.net/clapperboard/')
    .controller('MainCtrl', function (ItemsModel) {
        var main = this;

        function getItems() {
            ItemsModel.all()
                .then(function (result) {
                    main.items = result.data.movies;
                });
        }

        getItems();
    })
    .service('ItemsModel', function ($http, ENDPOINT_URI) {
        var service = this,
            path = 'movies?imdb_data=1';

        function getUrl() {
            return ENDPOINT_URI + path;
        }

        service.all = function () {
            return $http.get(getUrl());
        };
    });
