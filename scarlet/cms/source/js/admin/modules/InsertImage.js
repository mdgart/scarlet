define(
	[
		"./Insert",
		"$"
	],
	function (Insert, $) {

		"use strict";

		return Insert.extend({

			onInput : function (e) {

				var $target = $(e.currentTarget),
					attribute = $target.data('attribute'),
					value = $(e.currentTarget).val(),
					$preview = this.$dom.find(".image-preview"),
					$img = $preview.find('img');

				if (!$img.length) {

					$img = $("<img />");
					$preview.append($img);

					this.vars.$node = $img;

					$img.on("load", this.proxy(function (e) {

						var width = $img.width(),
							height = $img.height();

						this.vars.size.width = width;
						this.vars.size.height = height;

						this.setAttribute("width", width);
						this.setAttribute("height", height);

					}));

				} else {
					this.vars.$node = $img;
				}

				if (attribute === "width" || attribute === "height") {

					if (this.vars.constrain) {
						this.constrainProportion(attribute, value);
					}

					this.vars.size[attribute] = value;

				}

				this.vars.$node = $img.attr(attribute, value);

			}


		});

	});
