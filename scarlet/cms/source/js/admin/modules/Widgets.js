define(
	function (require, exports, module) {

		"use strict";

		var DOMClass             = require("rosy/base/DOMClass"),
			$                    = require("$"),
			jQuerySelect2        = require("$plugin!select2"),
			jQueryPickadate      = require("$plugin!pickadate"),
			AssetSelect          = require("./AssetSelect"),
			ApiSelect            = require("./ApiSelect"),
			Formset              = require("./Formset"),
			Tabs                 = require("./Tabs"),
			InsertVideo          = require("./InsertVideo"),
			InsertImage          = require("./InsertImage"),
			Wysiwyg              = require("./wysiwyg/Wysiwyg"),
			WidgetEvents         = require("./WidgetEvents"),
			WindowPopup          = require("./WindowPopup"),
			OnExit               = require("./OnExit");

		return DOMClass.extend({

			init : function (dom) {
				this.subscribe(WidgetEvents.RENDER, this._render);
			},

			_render : function (n) {
				var dom = $(n.data.dom);

				this._renderSelect(dom);
				this._renderAssetSelect(dom);
				this._renderFormset(dom);
				this._renderApiSelect(dom);
				this._renderDatePicker(dom);
				this._renderWysiwig(dom);
				this._renderTabs(dom);
				this._renderInsertVideo(dom);
				this._renderInsertImage(dom);

				this._handlePopup(dom);
			},

			_renderWysiwig : function (dom) {
				dom.find('.widget-wysiwyg').each(function (i, textarea) {
					var wysiwyg = new Wysiwyg($(textarea));
				});
			},

			_renderDatePicker : function (dom) {
				dom.find("[data-date-format]").each(function (i, el) {
					el = $(el);
					el.attr('placeholder', el.data('date-format').toUpperCase());
					if (!Modernizr.inputtypes.date) { // Use plugin if browser lacks native support for input type="date"
						el.pickadate({
							format: 'yyyy-mm-dd',
							format_submit: false,
							month_prev: 'w',
							month_next: 'e',
						});
					}
				});
			},

			_renderSelect : function (dom) {
				dom.find("select").select2({
					minimumResultsForSearch : 20
				});

				dom.find(".widget-tags").select2({
					tags: [],
					tokenSeparators : [',']
				});
			},

			_renderAssetSelect : function (dom) {
				dom.find(".widget-asset").each(function (i, dom) {
					var picker = new AssetSelect($(dom));
				});
			},

			_renderFormset : function (dom) {
				dom.find(".widget-formset").each(function (i, dom) {
					var formset = new Formset($(dom));
				});
			},

			_renderApiSelect : function (dom) {
				dom.find(".api-select").each(function (i, dom) {
					var select = new ApiSelect($(dom));
				});
			},

			_handlePopup : function (dom) {
				if (!window.opener) {
					return;
				}

				dom.find('.close-popup').click(function (i, dom) {
					window.close();
				});

				dom.find('.widget-popup-data').each(function (i, dom) {
					WindowPopup.respond($(dom).data());
				});
			},

			_renderTabs : function (dom) {
				dom.find(".widget-tabs").each(function (i, el) {
					var tabs = new Tabs($(el));
				});
			},

			_renderInsertVideo : function (dom) {
				dom.find(".widget-insert-video").each(function (i, el) {
					var insertVideo = new InsertVideo({
						$dom : $(el)
					});
				});
			},

			_renderInsertImage : function (dom) {
				dom.find(".widget-insert-image").each(function (i, el) {
					var insertImage = new InsertImage({
						$dom : $(el)
					});
				});
			},
		});
	}
);
