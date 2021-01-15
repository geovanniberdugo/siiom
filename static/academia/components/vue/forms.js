const inputMixin = {
    data () {
        return {
            errors: [],
            focused: false,
            tabFocused: false,
            lazyValue: this.value
        }
    },
    props: {
        disabled: Boolean,
        hint: String,
        label: String,
        required: Boolean,
        rules: {
            type: Array,
            default: () => []
        },
        value: {
            required: false,
        },
        placeholder: String,
    },
    computed: {
        hasError () {
            return this.errors.length !== 0;
        }
    },
    watch: {
        rules () {
            this.validate()
        }
    },
    mounted () {
        this.validate()
    },
    methods: {
        genLabel () {
            const data = {}
            if (this.id) data.attrs = {for: this.id}
            return this.$createElement('label', data, this.label)
        },
        toggle () {},
        genMessage () {

        },
        genHint () {

        },
        genError (error) {

        },
    }
}