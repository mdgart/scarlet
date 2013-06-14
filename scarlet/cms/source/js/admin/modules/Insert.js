define(
	[
		"rosy/base/DOMClass",
		"$",
		"admin/modules/WindowPopup"
	],
	function (DOMClass, $, WindowPopup) {

		"use strict";

		return DOMClass.extend({

			$dom : null,

			vars : {
				$inputs : null,
				$form : null,
				$node : false,
				constrain : false,
				size : {
					width : null,
					height : null
				}
			},

			init : function () {

				this.$dom = this.vars.$dom;
				this.vars.$inputs = this.$dom.find("[data-attribute]");
				this.vars.$form = this.$dom.find("form");

				this.bindInputs();
				this.sup();

			},

			bindInputs : function () {
				this.vars.$inputs.on("keypress paste", this.onDelayInput);
				this.vars.$form.on("submit", this.onSubmit);
				this.$dom.find(".constrain").on("change", this.onConstrainChange);
			},

			unbindInputs : function () {
				this.vars.$inputs.off();
			},

			// Helper to delay onInput call on paste
			// http://stackoverflow.com/a/1503425
			onDelayInput : function (e) {
				this.setTimeout(function () {
					this.onInput(e);
				});
			},

			onInput : function (e) {
				throw "You must override the `onInput` method.";
			},

			constrainProportion : function (dimension, value) {

				if (!this.vars.$node) {
					return;
				}

				var opposite = (dimension === "width") ? "height" : "width",
					oppositeValue = this.vars.size[opposite],
					ratio = ((value - this.vars.size[dimension]) / this.vars.size[dimension]) + 1;

				// Sets the opposing axis based on the ratio difference in value.
				this.vars.size[opposite] = Math.round(oppositeValue * ratio);

				// Updates the proportion attribute.
				this.setAttribute(opposite, this.vars.size[opposite]);

			},

			setAttribute : function (attr, val) {
				this.vars.$inputs.filter("[data-attribute=\"" + attr + "\"]").val(val);
				this.vars.$node.attr(attr, val);
			},

			// Sets the constrain value to the state of the check-box
			onConstrainChange : function (e) {
				this.vars.constrain = !!($(e.currentTarget).is(":checked"));
			},

			// Sends data back to the parent window.
			onSubmit : function (e) {
				e.preventDefault();
				WindowPopup.respond(this.vars.$node);
			},

			destroy : function () {
				this.unbindInputs();
				this.sup();
			}

		});

	}
);
