import bottle

@bottle.route('/hello')
def hello():
    return "Hello!!"

@bottle.route('/')
@bottle.route('/hello/<name>')
def greet(name='Stranger'):
    return bottle.template('Hello {{name}}, how are you??', name=name)

@bottle.route('/static/:filename#.*#')
def send_static(filename):
    return bottle.static_file(filename, root='static/')

@bottle.route('/')
def send_index():
    return send_static('index.html')

bottle.debug(True)
bottle.run(host="localhost", port=8080, debug=True, reloader=True)
