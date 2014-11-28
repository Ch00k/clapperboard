angular.module('Clapperboard', [])
    .constant('ENDPOINT_URI', 'http://127.0.0.1:5000/')
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
            path = 'movies?starting_within_days=14&imdb_data=1&theatre_id=3';

        function getUrl() {
            return ENDPOINT_URI + path;
        }

        service.all = function () {
            return $http.get(getUrl());
        };
    });
