// -*- coding: utf-8 flymake-gjshint:jshint -*-
var AG = {};

AG.Graph = function($base, AS) {
    this.scale = 25;
    
    this.base = $base;
    this.AS = AS;
    this.canvas = document.createElement('canvas');
    this.canvas.width = $base.width();
    this.canvas.height = $base.height();
    this.base.append(this.canvas);
    
    this.center = {x: this.canvas.width / 2, y: this.canvas.height / 2};
    
    this.ctx = this.canvas.getContext('2d');
    this.data = {};

    this.graph = new Springy.Graph();

    var self = this;
    this.layout = new Springy.Layout.ForceDirected(this.graph, 400.0, 400.0, 0.2);
    this.renderer = new Springy.Renderer(
        this.layout,
        function(){this.clear.apply(self, arguments);},
        function(){this.drawEdge.apply(self, arguments);},
        function(){this.drawNode.apply(self, arguments);}
    );
    return this;
};

AG.Graph.prototype.getNode = function(label, data) {
    var node = this.graph.nodeSet[label];
    if(!node) {
        node = new Springy.Node(label, $.extend({label:label}, data));
        this.graph.addNode(node);
    }
    return node;
};

AG.Graph.prototype.addEdge = function(src, dst) {
    src = this.getNode(src);
    dst = this.getNode(dst);
    return this.graph.newEdge(src, dst, {});
};

AG.Graph.prototype.addEdges = function(elist) {
    var ret = [];
    for(var i = 0, szi = elist.length; i < szi; i++) {
        ret.push(this.addEdge(elist[i][0], elist[i][1]));
    }
    return ret;
};

AG.Graph.prototype.clear = function() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
};

AG.Graph.prototype.norm = function(pt) {
    return {x: pt.x * this.scale + this.center.x,
            y: pt.y * this.scale + this.center.y};
};

AG.Graph.prototype.drawArrow = function(p1, p2) {
    p1 = new Springy.Vector(p1.x, p1.y);
    p2 = new Springy.Vector(p2.x, p2.y);
    
    var ctx = this.ctx;
    ctx.save();
    ctx.beginPath();
    ctx.translate(p2.x, p2.y);
    var norm = p2.subtract(p1).normalise();
    var rad = norm.x == 0 ? Math.PI / 2 : Math.atan(norm.y / norm.x);
    if(norm.x < 0) rad += Math.PI;
    ctx.rotate(rad + Math.PI);
    ctx.translate(20, 0);
    ctx.moveTo(0, 0);
    ctx.lineTo(10, 6);
    ctx.lineTo(10, -6);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
};

AG.Graph.prototype.drawEdge = function(edge, pt1, pt2) {
    var ctx = this.ctx;
    var p1 = this.norm(pt1),
        p2 = this.norm(pt2);
    // エッジ描画
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.closePath();
    ctx.stroke();
    this.drawArrow(p1, p2);
};

AG.Graph.prototype.drawNode = function(node, pt) {
    var ctx = this.ctx;
    var p = this.norm(pt);
    if(!!node.data.host)
        var icon = this.AS.dlIcon(node.data.name, node.data.host);
    
    ctx.beginPath();
    if(!icon) {
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2, true);
        ctx.fillText(node.data.name, p.x + 17, p.y);
    } else {
//        ctx.drawImage(icon.img, p.x - 15, p.y - 15);
        $(icon.content).css({top:p.y - 15, left:p.x - 15});
    }

    ctx.closePath();
    ctx.fill();
};

AG.AngelSight = function() {
    this.$post_list = $('#post-list');

    this.G = new AG.Graph($("#content"), this);

    this.actionInit();

    this.cache = {};

    return this;
};

AG.AngelSight.prototype.actionInit = function() {
    var self = this;
    this.mouseDown = false;
    this.mousePos = {x:0,y:0};

    $("#content").mousedown(function($e){
        self.mouseDown = true;
        self.mousePos = {x:$e.pageX, y:$e.pageY};
    }).mousemove(function($e){
        if(!self.mouseDown) return;
        var np = {x:$e.pageX, y:$e.pageY};
        self.G.center.x -= self.mousePos.x - np.x;
        self.G.center.y -= self.mousePos.y - np.y;
        self.mousePos = np;
        self.G.renderer.start();
    }).mouseup(function(ev){
        self.mouseDown = false;
    });
    
    $("#form-blog-form").submit(function(){
        console.log($("#form-blog-input").val());
        self.dlPosts($("#form-blog-input").val() + ".tumblr.com");
        $("#form-blog-input").val("");
        return false;
    });

    $("#scale-down-button").click(function(){
        if(self.G.scale > 10)
            self.G.scale -= 5;
        self.G.renderer.start();
    });
    $("#scale-up-button").click(function(){
        self.G.scale += 5;
        self.G.renderer.start();
    });
    $("#graph-start-button").click(function(){
        self.G.renderer.start();
    });
    $("#graph-stop-button").click(function(){
        self.G.renderer.stop();
    });
    
};

AG.AngelSight.prototype.start = function() {
    this.G.renderer.start();
};

AG.AngelSight.prototype.dlPosts = function(blog) {
    var self = this;
    $.ajax({
        dataType: 'json',
        url: 'api/post',
        data: {
            blog: blog
        },
        success: function(data) {
            var posts = data.response.posts.reverse();
            for(var i = 0, szi = posts.length; i < szi; i++) {
                var $li = $(document.createElement('li'))
                        .html($(posts[i].caption).children()[0])
                        .addClass('post-element')
                        .prependTo(self.$post_list)
                        .data(posts[i]);
                $li.click(function() {
                    self.postClick.apply(self, arguments);
                });
            }
        }
    });
    
};

AG.AngelSight.prototype.postClick = function(event, since) {
    var self = this;
    var $li = $(event.delegateTarget);
    since = !!since ? since : 0;
    
    $.ajax({
        dataType: 'json',
        url: 'api/note',
        data: {
            url: $li.data('post_url')
        },
        success: function(data) {
            function renderPosts(index) {
                if(index >= data.length) return;

                if(data[index].type == "reblog") {
                    var link = data[index].data,
                        src_data = {host: link[0].user_blog,
                                    name: link[0].user_name},
                        dst_data = {host: link[1].user_blog,
                                    name: link[1].user_name};
                    self.G.getNode(link[0].user_name, src_data);
                    self.G.getNode(link[1].user_name, dst_data);
                    self.G.addEdge(link[0].user_name, link[1].user_name);

                    self.dlIcon(link[0].user_name, link[0].user_blog);
                    self.dlIcon(link[1].user_name, link[1].user_blog);
                }

                window.setTimeout(function(){renderPosts(index + 1);}, 200);
            }

            data.reverse();
            data = data.filter(function(e) {
                return e.type == "reblog";
            });

            renderPosts(0);
        }
    });
};

AG.AngelSight.prototype.dlIcon = function(name, blog_host, callback) {
    var self = this;
    if(blog_host in this.cache) {
        return this.cache[blog_host];
    } else {
        var img = new Image();
        img.width = 30;
        img.height = 30;
        img.src = "http://api.tumblr.com/v2/blog/" + blog_host + "/avatar/" + 30;
        img.onload = function() {
            var $a = $('<a target="_blank"/>')
                    .attr('href', "http://" + blog_host)
                    .addClass('node-icon')
                    .appendTo($('#content'))
                    .append($(img))
                    .append($('<span class="node-name">'+ name +'</span>'));

            self.cache[blog_host] = {img: img, content:$a};

            if(!!callback) callback(self.cache[blog_host]);

            self.G.renderer.start();
        };
        return null;
    }
};
