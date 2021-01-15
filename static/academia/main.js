import Vue from 'vue/dist/vue.js';
import VueResource from 'vue-resource';


Vue.use(VueResource);

const app = new Vue({
    el: '#app',
    delimiters: ['{[', ']}'],
    data: {
        students: [],
    },
    mounted: function () {
        this._fetchStudents();
    },
    components: {
        // 'v-menu': MenuComponent,
        // 'edit-dialog': EditDialogComponent,
    },
    computed: {
        mainClasses: function () {
            return {
                table: true,
                'table-bordered': true,
            }
        },
        thClasses: function () {
            return {
                
            }
        }
    },
    methods: {
        _fetchStudents () {
            // this.$http.get()
            //     .then(response => {

            //     }, response => {

            //     })
            let students = [
                {
                    nombre: 'German',
                    sesiones: [
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: true,
                        },
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: true,
                        },
                    ]
                },
                {
                    nombre: 'Tania',
                    sesiones: [
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: true,
                        },
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: false,
                        },
                    ]
                },
                {
                    nombre: 'Geovanni',
                    sesiones: [
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: true,
                        },
                        {
                            nombre: '1',
                            nota: '4.3',
                            asistencia: false,
                        },
                    ]
                }
            ]
            // Vue.set(this, 'students', students);
            this.students = students;
            console.log(this.students);
        }
    }
});
