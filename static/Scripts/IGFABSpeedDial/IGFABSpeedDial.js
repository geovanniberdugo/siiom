/**
 * jQuery Material FAB Speed Dial
 * @author Tania Hernandez (Ingeniarte Soft.)
 * @requires jQuery 2.14 or later
 *
 * 2017, Tania Hernandez
 *
 * Test Page
 * See: http://siiom.net/grupo/organigrama
 */

// TODO cambiar el click por hover

 ;(function ($){
     $.fn.IGFABSpeedDial = function() {

         var $$ = $(this);
         var principal = $$.children("#fab-principal");
         var hijos = $$.children(".m-btn.child");

         principal.click(function() {
             if($(".backdrop").length) {
                 $(".backdrop").fadeOut(125);
                 $(".backdrop").remove();
                 hijos.css("bottom", principal.css("bottom"));
             }
             else {
                 $("body").append("<div class='backdrop'></div>");
                 $(".backdrop").fadeIn(125);
                 hijos.each(function(){
                     var pos = parseInt(principal.css("bottom")) + principal.outerHeight() + 55 * $(this).data("subfab") - hijos.outerHeight();
                     $(this).css("bottom", pos);
                 });
             }
             principal.children("i").toggleClass("zmdi-plus");
             principal.children("i").toggleClass("zmdi-close");
         });

         return $$;
     };
 })(jQuery);
